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
    ).with_for_update().first()

    # 4. Kiểm tra thời gian hủy
    now = now_vietnam()
    deadline = campaign.start_time - timedelta(hours=24)

    if now > deadline:
        raise HTTPException(
            status_code=400,
            detail="Chỉ được hủy trước giờ bắt đầu ít nhất 24 giờ"
        )

    # 5. Cập nhật trạng thái
    was_approved = registration.status == "APPROVED"
    registration.status = "CANCELLED"
    try:
        # Hủy đăng ký đã duyệt tạo chỗ trống; mời người đầu hàng ngay.
        if was_approved:
            promote_after_vacancy(db, registration.campaign_id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(registration)

    return registration

def approve_registration(
        db: Session,
        registration_id : int ,
        campaign_id : int
): 
    try:
        # Thứ tự khóa thống nhất: User -> Campaign (như create_registration).
        # Lấy user_id trước khi khóa; sau khi khóa phải kiểm tra lại trạng thái đơn.
        registration_user_id = db.query(RegistrationModel.user_id).filter(
            RegistrationModel.id == registration_id,
            RegistrationModel.campaign_id == campaign_id
        ).scalar()
        if registration_user_id is None:
            raise HTTPException(404, "Không tìm thấy đăng ký")

        user = db.query(UserModel).filter(
            UserModel.id == registration_user_id
        ).with_for_update().first()
        if user is None:
            raise HTTPException(404, "Không tìm thấy người đăng ký")

        campaign = db.query(CampaignModel).filter(
            CampaignModel.id == campaign_id
        ).with_for_update().first()
        if not campaign:
            raise HTTPException(404, "Không tìm thấy chiến dịch")
        if campaign.status != "OPEN":
            raise HTTPException(400, "Chiến dịch không còn mở đăng ký")
        if campaign.registration_deadline < now_vietnam():
            raise HTTPException(400, "Chiến dịch đã hết hạn đăng ký")

        registration = db.query(RegistrationModel).filter(RegistrationModel.id == registration_id,RegistrationModel.campaign_id == campaign_id).first()

        if not registration :
            raise HTTPException(404,"không tìm thấy đăng ký")

        # 3. chỉ duyệt đơn đang chờ 
        if registration.status != "PENDING" :
            raise HTTPException(400,"Đăng ký không ở trạng thái chờ duyệt")

        # Kiểm tra lại trùng lịch ngay lúc duyệt, không chỉ lúc đăng ký.
        approved_registrations = db.query(RegistrationModel).join(
            CampaignModel, RegistrationModel.campaign_id == CampaignModel.id
        ).filter(
            RegistrationModel.user_id == registration.user_id,
            RegistrationModel.status == "APPROVED",
            RegistrationModel.id != registration.id,
            CampaignModel.start_time < campaign.end_time,
            CampaignModel.end_time > campaign.start_time
        ).first()
        if approved_registrations:
            raise HTTPException(400, "Lịch chiến dịch bị trùng với chiến dịch đã được duyệt")

        #4. đếm số người đã được duyệt
        approve_count = db.query(RegistrationModel).filter(
            RegistrationModel.campaign_id == campaign_id,
            RegistrationModel.status == "APPROVED"
        ).count()

        #5. kiểm tra giới hạn về số lượng
        active_invites = db.query(WaitlistEntryModel).filter(
            WaitlistEntryModel.campaign_id == campaign_id,
            WaitlistEntryModel.status == "INVITED",
            WaitlistEntryModel.response_deadline > now_vietnam(),
        ).count()
        if approve_count + active_invites >= campaign.max_participants:
            raise HTTPException (400,"chiến dịch đã đủ số lượng người tham gia")

        registration.status = "APPROVED"
        registration.rejection_reason = None

        create_notification(
            db=db,
            user_id=registration.user_id,
            title="Đăng ký chiến dịch được duyệt",
            content=f'Đăng ký tham gia chiến dịch "{campaign.title}" đã được duyệt.',
            link=f"user-dashboard.html?tab=overview&campaign_id={campaign_id}",
        )
        db.commit()
        db.refresh(registration)

        return {
    "message": "Duyệt đăng ký thành công",
    "registration_id": registration.id,
    "campaign_id": registration.campaign_id,
    "status": registration.status
}
    except HTTPException:
        db.rollback()
        raise

    except Exception :
        db.rollback()
        raise

def reject_registration(
        db: Session,
        registration_id : int ,
        campaign_id : int ,
        reason : str 
):
    registration = db.query(RegistrationModel).filter(
        RegistrationModel.id == registration_id,
        RegistrationModel.campaign_id == campaign_id
    ).first()

    if not registration:
        raise HTTPException(404,"không tìm thấy đăng ký") 
    if registration.status != "PENDING" :
        raise HTTPException (400, " đăng ký không ở trạng thái chờ duyệt")

    if not reason or not reason.strip():
        raise HTTPException(400,"Vui lòng nhập lý do từ chối")

    try :
        registration.status = "REJECTED"
        registration.rejection_reason = reason.strip()

        # Nếu đang có chỗ trống, chuyển lời mời cho người đầu hàng.
        promote_after_vacancy(db, campaign_id)

        db.commit()
        db.refresh(registration)

        return registration
    except Exception:
        db.rollback()
        raise

def get_campaign_registrations(
    db: Session,
    campaign_id: int,
    status: str = None
):
    query = (
        db.query(RegistrationModel)
        .options(joinedload(RegistrationModel.user))
        .filter(RegistrationModel.campaign_id == campaign_id)
    )

    if status:
        query = query.filter(
            RegistrationModel.status == status
        )

    regs = query.order_by(RegistrationModel.id.desc()).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "campaign_id": r.campaign_id,
            "status": r.status,
            "message": r.message,
            "rejection_reason": r.rejection_reason,
            "created_at": r.created_at,
            "user_name": r.user.full_name if r.user else None,
            "user_email": r.user.email if r.user else None,
            "user_phone": r.user.phone if r.user else None,
        }
        for r in regs
    ]


def get_my_registrations(db: Session, user_id: int):
    regs = (
        db.query(RegistrationModel)
        .options(joinedload(RegistrationModel.campaign))
        .filter(RegistrationModel.user_id == user_id)
        .order_by(RegistrationModel.id.desc())
        .all()
    )

    return [
        {
            "id": r.id,
            "campaign_id": r.campaign_id,
            "campaign_title": r.campaign.title if r.campaign else f"Chiến dịch #{r.campaign_id}",
            "status": r.status,
            "message": r.message,
            "rejection_reason": r.rejection_reason,
            "created_at": r.created_at,
        }
        for r in regs
    ]
