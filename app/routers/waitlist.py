from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.campaigns import CampaignModel, now_vietnam
from app.models.organizations import OrganizationModel
from app.models.registration import RegistrationModel
from app.models.users import UserModel
from app.models.waitlist_entry import WaitlistEntryModel
from app.schemas.waitlist_entry import WaitlistEntryResponse
from app.services.notifications import create_notification


router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


def require_open_campaign(campaign: CampaignModel, now):
    if campaign.status != "OPEN" or campaign.registration_deadline <= now:
        raise HTTPException(409, "Chiến dịch đã đóng đăng ký.")


def has_registration(db: Session, user_id: int, campaign_id: int):
    return db.query(RegistrationModel.id).filter(
        RegistrationModel.user_id == user_id,
        RegistrationModel.campaign_id == campaign_id,
        RegistrationModel.status != "CANCELLED",
    ).first() is not None


@router.get("/mine", response_model=list[WaitlistEntryResponse])
def my_entries(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return db.query(WaitlistEntryModel).filter_by(user_id=current_user.id).all()


@router.post("/campaign/{campaign_id}", response_model=WaitlistEntryResponse)
def join_waitlist(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("USER")),
):
    campaign = db.query(CampaignModel).filter_by(id=campaign_id).with_for_update().first()
    if campaign is None:
        raise HTTPException(404, "Không tìm thấy chiến dịch.")
    now = now_vietnam()
    require_open_campaign(campaign, now)
    if has_registration(db, current_user.id, campaign_id):
        raise HTTPException(409, "Bạn đã đăng ký chiến dịch này.")

    entry = db.query(WaitlistEntryModel).filter_by(
        user_id=current_user.id, campaign_id=campaign_id
    ).first()
    if entry and entry.status in ("WAITING", "INVITED"):
        return entry
    position = db.query(func.max(WaitlistEntryModel.position)).filter_by(campaign_id=campaign_id).scalar()
    if entry is None:
        entry = WaitlistEntryModel(user_id=current_user.id, campaign_id=campaign_id)
        db.add(entry)
    entry.position = (position or 0) + 1
    entry.status = "WAITING"
    entry.invited_at = None
    entry.response_deadline = None
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/managed")
def managed_entries(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    rows = db.query(WaitlistEntryModel).join(WaitlistEntryModel.campaign).join(
        CampaignModel.organization
    ).options(joinedload(WaitlistEntryModel.campaign), joinedload(WaitlistEntryModel.user)).filter(
        OrganizationModel.owner_id == current_user.id
    ).order_by(WaitlistEntryModel.campaign_id, WaitlistEntryModel.position).all()
    now = now_vietnam()
    return [
        WaitlistEntryResponse.model_validate(row).model_dump() | {
            "campaign_title": row.campaign.title,
            "user_name": row.user.full_name,
            "can_invite": row.campaign.status == "OPEN" and row.campaign.registration_deadline > now and (
                row.status == "WAITING" or (
                    row.status == "INVITED" and row.response_deadline and row.response_deadline <= now
                )
            ),
        }
        for row in rows
    ]


@router.patch("/{entry_id}/invite", response_model=WaitlistEntryResponse)
def invite(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ORGANIZER")),
):
    campaign = db.query(CampaignModel).join(CampaignModel.organization).join(
        WaitlistEntryModel, WaitlistEntryModel.campaign_id == CampaignModel.id
    ).filter(
        OrganizationModel.owner_id == current_user.id, WaitlistEntryModel.id == entry_id,
    ).with_for_update().first()
    if campaign is None:
        raise HTTPException(404, "Không tìm thấy mục trong danh sách chờ.")
    now = now_vietnam()
    require_open_campaign(campaign, now)
    entry = db.get(WaitlistEntryModel, entry_id)
    if entry.status == "INVITED" and entry.response_deadline and entry.response_deadline > now:
        return entry
    if entry.status not in ("WAITING", "INVITED") or has_registration(db, entry.user_id, campaign.id):
        raise HTTPException(409, "Tình nguyện viên không còn trong hàng chờ.")

    entry.status = "INVITED"
    entry.invited_at = now
    entry.response_deadline = min(now + timedelta(hours=24), campaign.registration_deadline)
    create_notification(
        db, entry.user_id,
        "Lời mời đăng ký chiến dịch",
        f'Bạn được mời gửi đơn cho chiến dịch "{campaign.title}" trước '
        f'{entry.response_deadline:%H:%M %d/%m/%Y} (giờ Việt Nam).',
        f"user-dashboard.html?tab=campaigns&campaign_id={campaign.id}",
    )
    db.commit()
    db.refresh(entry)
    return entry
