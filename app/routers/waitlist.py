from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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


@router.get("/mine", response_model=list[WaitlistEntryResponse])
def my_entries(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    process_expired_invites(db)
    return db.query(WaitlistEntryModel).filter_by(
        user_id=current_user.id
    ).order_by(WaitlistEntryModel.created_at.desc()).all()


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
    return entry


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
    return list_campaign_waitlist(db, campaign_id)


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
    return respond_to_invite(db, entry_id, current_user.id, response)
