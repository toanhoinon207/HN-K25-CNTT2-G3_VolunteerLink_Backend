import secrets
import string
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.campaigns import CampaignModel
from app.models.organizations import OrganizationModel
from app.models.registration import RegistrationModel
from app.models.attendances import AttendanceModel
from app.schemas.attendances import (
    ManualAttendanceCreate,
    AttendanceStatusUpdate,
    AttendanceTimeUpdate
)



def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None) 

def normalize_vietnam_datetime(value):
    if value is None:
        return None

    if value.tzinfo is not None:
        value = value.astimezone(
            ZoneInfo("Asia/Ho_Chi_Minh")
        ).replace(tzinfo=None)

    return value 


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
        attendance.total_minutes = max(
            0,
            int(round((now - attendance.check_in_at).total_seconds() / 60))
        )

        db.commit()
        db.refresh(attendance)

        return attendance

    except Exception:
        db.rollback()
        raise


# =====================================================
# ORGANIZER: KIỂM TRA QUYỀN SỞ HỮU CHIẾN DỊCH
# =====================================================

def check_organizer_campaign(db, campaign_id, current_user):
    campaign = get_campaign(db, campaign_id)

    organization = db.query(OrganizationModel).filter(
        OrganizationModel.id == campaign.organization_id,
        OrganizationModel.owner_id == current_user.id
    ).first()

    if organization is None:
        raise HTTPException(
            status_code=403,
            detail="Bạn không có quyền quản lý chiến dịch này"
        )

    return campaign


# =====================================================
# ORGANIZER: LẤY DANH SÁCH TNV ĐÃ ĐƯỢC DUYỆT
# =====================================================

def get_campaign_attendances(db, campaign_id, current_user):

    campaign = check_organizer_campaign(
        db, campaign_id, current_user
    )

    registrations = db.query(RegistrationModel).options(
        joinedload(RegistrationModel.user),
        joinedload(RegistrationModel.attendance)
    ).filter(
        RegistrationModel.campaign_id == campaign_id,
        RegistrationModel.status == "APPROVED"
    ).all()

    result = []

    for registration in registrations:
        user = registration.user
        attendance = registration.attendance

        volunteer_name = (
            getattr(user, "full_name", None)
            or getattr(user, "name", None)
            or getattr(user, "username", None)
            or f"Tình nguyện viên #{registration.user_id}"
        )

        result.append({
            "registration_id": registration.id,
            "volunteer_id": registration.user_id,
            "volunteer_name": volunteer_name,

            "attendance_id": attendance.id if attendance else None,
            "status": attendance.status if attendance else None,
            "check_in_at": attendance.check_in_at if attendance else None,
            "check_out_at": attendance.check_out_at if attendance else None,
            "total_minutes": attendance.total_minutes if attendance else 0
        })

    return result


# =====================================================
# ORGANIZER: ĐIỂM DANH THỦ CÔNG
# =====================================================

def manual_attendance(db, campaign_id, data, current_user):
    try:
        check_organizer_campaign(
            db, campaign_id, current_user
        )

        registration = db.query(RegistrationModel).filter(
            RegistrationModel.id == data.registration_id,
            RegistrationModel.campaign_id == campaign_id,
            RegistrationModel.status == "APPROVED"
        ).with_for_update().first()

        if registration is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy đăng ký đã được duyệt"
            )

        existing = db.query(AttendanceModel).filter(
            AttendanceModel.registration_id == registration.id
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Tình nguyện viên đã có bản ghi điểm danh"
            )

        now = now_vietnam()

        attendance = AttendanceModel(
            registration_id=registration.id,
            status=data.status,
            check_in_at=now if data.status == "PRESENT" else None,
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
        raise HTTPException(
            status_code=409,
            detail="Bản ghi điểm danh đã tồn tại"
        )

    except Exception:
        db.rollback()
        raise


# =====================================================
# ORGANIZER: CẬP NHẬT TRẠNG THÁI CÓ MẶT / VẮNG MẶT
# =====================================================

def update_attendance_status(
    db, attendance_id, data, current_user
):
    try:
        attendance = db.query(AttendanceModel).filter(
            AttendanceModel.id == attendance_id
        ).with_for_update().first()

        if attendance is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy bản ghi điểm danh"
            )

        registration = db.query(RegistrationModel).filter(
            RegistrationModel.id == attendance.registration_id
        ).first()

        if registration is None:
            raise HTTPException(404, "Không tìm thấy đăng ký")

        check_organizer_campaign(
            db, registration.campaign_id, current_user
        )

        now = now_vietnam()

        attendance.status = data.status
        attendance.updated_by = current_user.id
        attendance.updated_at = now
        attendance.edit_reason = data.reason.strip()

        if data.status == "ABSENT":
            attendance.check_in_at = None
            attendance.check_out_at = None
            attendance.total_minutes = 0

        elif data.status == "PRESENT":
            if attendance.check_in_at is None:
                attendance.check_in_at = now

        db.commit()
        db.refresh(attendance)

        return attendance

    except Exception:
        db.rollback()
        raise


# =====================================================
# ORGANIZER: CHỈNH SỬA GIỜ CHECK-IN / CHECK-OUT
# =====================================================

def update_attendance_time(
    db, attendance_id, data, current_user
):
    try:
        attendance = db.query(AttendanceModel).filter(
            AttendanceModel.id == attendance_id
        ).with_for_update().first()

        if attendance is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy bản ghi điểm danh"
            )

        registration = db.query(RegistrationModel).filter(
            RegistrationModel.id == attendance.registration_id
        ).first()

        if registration is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy đăng ký"
            )

        check_organizer_campaign(
            db, registration.campaign_id, current_user
        )

        if attendance.status != "PRESENT":
            raise HTTPException(
                status_code=400,
                detail="Chỉ được chỉnh sửa thời gian của TNV có mặt"
            )

        # Chỉ cập nhật những trường được gửi lên
        if "check_in_at" in data.model_fields_set:
            attendance.check_in_at = normalize_vietnam_datetime(
                data.check_in_at
            )

        if "check_out_at" in data.model_fields_set:
            attendance.check_out_at = normalize_vietnam_datetime(
                data.check_out_at
            )

        # Chuẩn hóa cả dữ liệu cũ trước khi so sánh
        check_in = normalize_vietnam_datetime(
            attendance.check_in_at
        )

        check_out = normalize_vietnam_datetime(
            attendance.check_out_at
        )

        if check_out is not None and check_in is None:
            raise HTTPException(
                status_code=400,
                detail="Phải có giờ check-in trước khi ghi nhận check-out"
            )

        if check_in is not None and check_out is not None:
            if check_out <= check_in:
                raise HTTPException(
                    status_code=400,
                    detail="Giờ check-out phải sau giờ check-in"
                )

            attendance.total_minutes = max(
                0,
                int(round((check_out - check_in).total_seconds() / 60))
            )
        else:
            attendance.total_minutes = 0

        attendance.check_in_at = check_in
        attendance.check_out_at = check_out

        attendance.updated_by = current_user.id
        attendance.updated_at = now_vietnam()
        attendance.edit_reason = data.reason.strip()

        db.commit()
        db.refresh(attendance)

        return attendance

    except Exception:
        db.rollback()
        raise


def get_my_attendance_history(db: Session, user_id: int):
    attendances = (
        db.query(AttendanceModel)
        .join(RegistrationModel, AttendanceModel.registration_id == RegistrationModel.id)
        .options(
            joinedload(AttendanceModel.registration).joinedload(RegistrationModel.campaign)
        )
        .filter(RegistrationModel.user_id == user_id)
        .order_by(AttendanceModel.id.desc())
        .all()
    )

    result = []
    for att in attendances:
        reg = att.registration
        camp = reg.campaign if reg else None
        result.append({
            "id": att.id,
            "registration_id": att.registration_id,
            "campaign_id": camp.id if camp else None,
            "campaign_title": camp.title if camp else f"Chiến dịch #{att.registration_id}",
            "check_in_at": att.check_in_at,
            "check_out_at": att.check_out_at,
            "total_minutes": att.total_minutes,
            "status": att.status,
        })
    return result