from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.models.registration import RegistrationModel
from app.models.campaigns import CampaignModel
from app.models.users import UserModel
from app.services.campaigns import close_expired_campaigns
from app.models.waitlist_entry import WaitlistEntryModel
from app.services.notifications import create_notification
from app.services.waitlist import add_to_waitlist, approved_count, active_invite_count, promote_after_vacancy

def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)


def create_registration(db : Session, user_id : int , campaign_id : int , message : str = None) :
    close_expired_campaigns(db)

    # Khóa theo người dùng để tránh hai yêu cầu đăng ký đồng thời.
    db.query(UserModel).filter(UserModel.id == user_id).with_for_update().first()

    # 1. kiểm tra chiến dịch có tồn tại kh 
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).with_for_update().first()
    if campaign is None : 
        raise HTTPException(status_code=404, detail="Không tìm thấy chiến dịch")

    if campaign.status != "OPEN":
        raise HTTPException(status_code=400, detail="Chiến dịch chưa mở hoặc đã đóng")

    # 3 . kiểm tra thời hạn đăng ký 
    now = now_vietnam()

    if campaign.registration_deadline < now :
        raise HTTPException(status_code=400, detail="Chiến dịch đã hết hạn đăng ký")

    # 4. Kiểm tra đăng ký trùng
    old_registration = db.query(RegistrationModel).filter(
        RegistrationModel.user_id == user_id,
        RegistrationModel.campaign_id == campaign_id
    ).first()

    if old_registration:
        if old_registration.status != "CANCELLED":
            raise HTTPException(status_code=400, detail="Bạn đã đăng ký chiến dịch này")

    # 5. Kiểm tra trùng lịch với chiến dịch đã được duyệt
    registrations = db.query(RegistrationModel).join(
        CampaignModel,
        RegistrationModel.campaign_id == CampaignModel.id
    ).filter(
        RegistrationModel.user_id == user_id,
        RegistrationModel.status == "APPROVED"
    ).all()

    for item in registrations:
        old_campaign = item.campaign

        # Kiểm tra thời gian bị trùng
        if (old_campaign.start_time < campaign.end_time
                and old_campaign.end_time > campaign.start_time):

            raise HTTPException(
                status_code=400,
                detail="Lịch chiến dịch bị trùng với chiến dịch đã được duyệt"
            )

    # Chiến dịch đã đủ chỗ: ghi nhận đăng ký và xếp hàng tự động.
    if approved_count(db, campaign_id) + active_invite_count(db, campaign_id) >= campaign.max_participants:
        if old_registration:
            old_registration.status = "WAITLISTED"
            old_registration.message = message
            old_registration.rejection_reason = None
            old_registration.created_at = now
            registration = old_registration
        else:
            registration = RegistrationModel(
                user_id=user_id, campaign_id=campaign_id,
                status="WAITLISTED", message=message,
            )
            db.add(registration)
        add_to_waitlist(db, user_id, campaign_id)
        db.commit()
        db.refresh(registration)
        return registration

    waitlist_entry = db.query(WaitlistEntryModel).filter_by(
    user_id=user_id,
    campaign_id=campaign_id
    ).first()

    # Nếu người dùng đăng ký lại theo luồng thông thường,
    # xóa bản ghi hàng chờ cũ để tránh bị trùng.
    if old_registration and old_registration.status == "WAITLISTED":
        if waitlist_entry:
            db.delete(waitlist_entry)
            waitlist_entry = None

    if old_registration and old_registration.status in ("CANCELLED", "WAITLISTED"):
        old_registration.status = "PENDING"
        old_registration.message = message
        old_registration.rejection_reason = None
        old_registration.created_at = now

        db.commit()
        db.refresh(old_registration)
        return old_registration

    # 6. Tạo đăng ký mới
    registration = RegistrationModel(
        user_id=user_id,
        campaign_id=campaign_id,
        status="PENDING",
        message=message
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    return registration

def cancel_registration(db: Session, registration_id: int, user_id: int):

    # 1. Tìm đăng ký
    registration = db.query(RegistrationModel).filter(