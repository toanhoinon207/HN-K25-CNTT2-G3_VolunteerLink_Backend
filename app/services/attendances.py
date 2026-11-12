import secrets
import string
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.campaigns import CampaignModel
from app.models.organizations import OrganizationModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel



def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None) 


def generate_code():
    characters = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(characters) for _ in range(6))


def get_campaign(db: Session, campaign_id: int):
    campaign = db.query(CampaignModel).filter(
        CampaignModel.id == campaign_id
    ).first()

    if campaign is None:
        raise HTTPException(404, "Chiến dịch không tồn tại")

    return campaign


def validate_campaign_time(campaign, now):
    if now < campaign.start_time:
        raise HTTPException(400, "Chiến dịch chưa bắt đầu")

    if now > campaign.end_time:
        raise HTTPException(400, "Chiến dịch đã kết thúc")

    if campaign.status in ("CANCELLED", "DRAFT", "PENDING", "COMPLETED"):
        raise HTTPException(400, "Chiến dịch không cho phép điểm danh")


def validate_code(campaign, code, now):
    if campaign.attendance_code is None:
        raise HTTPException(400, "Chiến dịch chưa có mã điểm danh")

    if (
        campaign.attendance_code_expires_at is None
        or now >= campaign.attendance_code_expires_at
    ):
        raise HTTPException(400, "Mã điểm danh đã hết hạn")

    if not secrets.compare_digest(campaign.attendance_code, code):
        raise HTTPException(400, "Mã điểm danh không hợp lệ")


def get_approved_registration(db, campaign_id, user_id):
    registration = db.query(RegistrationModel).filter(
        RegistrationModel.campaign_id == campaign_id,
        RegistrationModel.user_id == user_id,
        RegistrationModel.status == "APPROVED"
    ).with_for_update().first()

    if registration is None:
        raise HTTPException(
            403,
            "Bạn chưa được duyệt tham gia chiến dịch"
        )

    return registration


def create_attendance_code(db, data, current_user):
    try:
        campaign = get_campaign(db, data.campaign_id)
        now = now_vietnam()

        organization = db.query(OrganizationModel).filter(
            OrganizationModel.id == campaign.organization_id,
            OrganizationModel.owner_id == current_user.id
        ).first()

        if organization is None:
            raise HTTPException(
                403,
                "Bạn không có quyền tạo mã cho chiến dịch này"
            )

        validate_campaign_time(campaign, now)

        code = generate_code()
        while db.query(CampaignModel).filter(
            CampaignModel.attendance_code == code,
            CampaignModel.id != campaign.id
        ).first() is not None:
            code = generate_code()

        expires_at = min(
            now + timedelta(minutes=data.expires_minutes),
            campaign.end_time
        )

        campaign.attendance_code = code
        campaign.attendance_code_expires_at = expires_at

        db.commit()

        return {
            "code": code,
            "expires_at": expires_at
        }

    except Exception:
        db.rollback()
        raise


def check_in(db, data, current_user):
    try:
        campaign = get_campaign(db, data.campaign_id)
        now = now_vietnam()

        validate_campaign_time(campaign, now)

        registration = get_approved_registration(
            db, data.campaign_id, current_user.id
        )

        validate_code(campaign, data.code, now)

        existing = db.query(AttendanceModel).filter(
            AttendanceModel.registration_id == registration.id
        ).first()

        if existing is not None:
            raise HTTPException(409, "Bạn đã check-in trước đó")

        attendance = AttendanceModel(
            registration_id=registration.id,
            check_in_at=now,
            check_out_at=None,
            total_minutes=0,
            recorded_by=current_user.id
        )

        db.add(attendance)
        db.commit()
        db.refresh(attendance)

        return attendance

    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bạn đã check-in trước đó")

    except Exception:
        db.rollback()
        raise


def check_out(db, data, current_user):
    try:
        campaign = get_campaign(db, data.campaign_id)
        now = now_vietnam()

        validate_campaign_time(campaign, now)

        registration = get_approved_registration(
            db, data.campaign_id, current_user.id
        )

        validate_code(campaign, data.code, now)

        attendance = db.query(AttendanceModel).filter(
            AttendanceModel.registration_id == registration.id
        ).with_for_update().first()

        if attendance is None or attendance.check_in_at is None:
            raise HTTPException(400, "Bạn chưa check-in")

        if attendance.check_out_at is not None:
            raise HTTPException(409, "Bạn đã check-out trước đó")

        attendance.check_out_at = now
        attendance.total_minutes = int(
            (now - attendance.check_in_at).total_seconds() // 60
        )

        db.commit()
        db.refresh(attendance)

        return attendance

    except Exception:
        db.rollback()
        raise 