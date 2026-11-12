from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.registration import RegistrationModel
from app.models.campaigns import CampaignModel


def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)


def create_registration(db : Session, user_id : int , campaign_id : int , message : str = None) :

    # 1. kiểm tra chiến dịch có tồn tại kh 
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
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

    if old_registration and old_registration.status == "CANCELLED":
        old_registration.status = "PENDING"
        old_registration.message = message
        old_registration.rejection_reason = None
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
        RegistrationModel.id == registration_id,
        RegistrationModel.user_id == user_id
    ).first()

    if registration is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy đăng ký")

    # 2. Kiểm tra trạng thái đăng ký
    if registration.status not in ["PENDING", "APPROVED"]:
        raise HTTPException(
            status_code=400,
            detail="Không thể hủy đăng ký này"
        )

    # 3. Lấy thông tin chiến dịch
    campaign = db.query(CampaignModel).filter(
        CampaignModel.id == registration.campaign_id
    ).first()

    # 4. Kiểm tra thời gian hủy
    now = now_vietnam()
    deadline = campaign.start_time - timedelta(hours=24)

    if now > deadline:
        raise HTTPException(
            status_code=400,
            detail="Chỉ được hủy trước giờ bắt đầu ít nhất 24 giờ"
        )

    # 5. Cập nhật trạng thái
    registration.status = "CANCELLED"

    db.commit()
    db.refresh(registration)

    return registration
