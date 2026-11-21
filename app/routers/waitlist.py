from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.campaigns import CampaignModel, now_vietnam
from app.models.registration import RegistrationModel
from app.models.users import UserModel
from app.models.waitlist_entry import WaitlistEntryModel
from app.schemas.waitlist_entry import WaitlistEntryResponse, WaitlistResponseRequest
from app.services.waitlist import (
    add_to_waitlist, approved_count, active_invite_count, list_campaign_waitlist,
    process_expired_invites, respond_to_invite,
)

router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


def entry_details(db: Session, entry: WaitlistEntryModel) -> dict:
    # Queue position reflects only active waiting entries, not historical sequence numbers.
    position = None
    if entry.status == "WAITING":
        position = db.query(WaitlistEntryModel).filter(
            WaitlistEntryModel.campaign_id == entry.campaign_id,
            WaitlistEntryModel.status == "WAITING",
            (WaitlistEntryModel.position < entry.position) |
            ((WaitlistEntryModel.position == entry.position) & (WaitlistEntryModel.id <= entry.id)),
        ).count()
    return {
        "id": entry.id, "user_id": entry.user_id, "campaign_id": entry.campaign_id,
        "position": entry.position, "queue_position": position,
        "status": entry.status, "invited_at": entry.invited_at,
        "response_deadline": entry.response_deadline, "responded_at": entry.responded_at,
        "created_at": entry.created_at,
        "campaign_title": entry.campaign.title if entry.campaign else None,
        "user_name": entry.user.full_name if entry.user else None,
    }



@router.get("/mine", response_model=list[WaitlistEntryResponse])
def my_entries(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    entries = db.query(WaitlistEntryModel).options(
        joinedload(WaitlistEntryModel.campaign)
    ).filter_by(user_id=current_user.id).order_by(WaitlistEntryModel.created_at.desc()).all()
    return [entry_details(db, entry) for entry in entries]


@router.post("/campaign/{campaign_id}", response_model=WaitlistEntryResponse)
def join_waitlist(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("USER")),
):
    process_expired_invites(db)
    campaign = db.query(CampaignModel).filter_by(id=campaign_id).with_for_update().first()
    if campaign is None:
        raise HTTPException(404, "Không tìm thấy chiến dịch")
    if campaign.status != "OPEN" or campaign.registration_deadline <= now_vietnam():
        raise HTTPException(409, "Chiến dịch đã đóng đăng ký")
    if approved_count(db, campaign_id) + active_invite_count(db, campaign_id) < campaign.max_participants:
        raise HTTPException(409, "Chiến dịch vẫn còn chỗ; hãy đăng ký theo luồng thông thường")
    registration = db.query(RegistrationModel).filter_by(
        user_id=current_user.id, campaign_id=campaign_id
    ).first()
    if registration and registration.status not in ("CANCELLED", "WAITLISTED"):
        raise HTTPException(409, "Bạn đã đăng ký chiến dịch này")
    entry = add_to_waitlist(db, current_user.id, campaign_id)
    if registration is None or registration.status == "CANCELLED":
        if registration is None:
            registration = RegistrationModel(
                user_id=current_user.id, campaign_id=campaign_id, status="WAITLISTED"
            )
            db.add(registration)
        else:
            registration.status = "WAITLISTED"
    db.commit()
    db.refresh(entry)
    return entry_details(db, entry)


@router.get("/campaign/{campaign_id}", response_model=list[WaitlistEntryResponse])
def campaign_waitlist(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    process_expired_invites(db)
    campaign = db.query(CampaignModel).join(CampaignModel.organization).filter(
        CampaignModel.id == campaign_id
    ).first()
    if campaign is None or campaign.organization.owner_id != current_user.id:
        raise HTTPException(403, "Bạn không có quyền xem danh sách chờ này")
    entries = db.query(WaitlistEntryModel).options(
        joinedload(WaitlistEntryModel.campaign), joinedload(WaitlistEntryModel.user)
    ).filter_by(campaign_id=campaign_id).order_by(
        WaitlistEntryModel.position, WaitlistEntryModel.id
    ).all()
    return [entry_details(db, entry) for entry in entries]


@router.patch("/{entry_id}/respond", response_model=WaitlistEntryResponse)
def respond(
    entry_id: int,
    request: WaitlistResponseRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("USER")),
):
    process_expired_invites(db)
    response = request.response.upper()
    if response not in ("ACCEPTED", "DECLINED"):
        raise HTTPException(422, "response phải là ACCEPTED hoặc DECLINED")
    entry = respond_to_invite(db, entry_id, current_user.id, response)
    return entry_details(db, entry)
