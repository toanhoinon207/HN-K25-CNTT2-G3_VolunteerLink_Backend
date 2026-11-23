import secrets
import string
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.campaigns import CampaignModel
from app.models.attendance_code_issues import AttendanceCodeIssueModel
from app.models.certificate import CertificateModel
from app.models.hourclaims import HourClaimModel
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


def validate_code(campaign, code, now, expected_type):
    if campaign.attendance_code is None:
        raise HTTPException(400, "Chiến dịch chưa có mã điểm danh")

    if (
        campaign.attendance_code_expires_at is None
        or now >= campaign.attendance_code_expires_at
    ):
        raise HTTPException(400, "Mã điểm danh đã hết hạn")

    # Không dùng mã CHECK-IN để CHECK-OUT hoặc ngược lại.
    # Mã cũ (type=NULL) phải được cấp lại theo loại rõ ràng.
    if campaign.attendance_code_type != expected_type:
        raise HTTPException(400, f"Cần mã {expected_type} hợp lệ")

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
        campaign = db.query(CampaignModel).filter(
            CampaignModel.id == data.campaign_id
        ).with_for_update().first()
        if campaign is None:
            raise HTTPException(404, "Chiến dịch không tồn tại")
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

        # If an active code of the requested type exists, return the same code.
        # No silent rotation and no duplicate issue on a retry / refresh.
        current_issue = (db.query(AttendanceCodeIssueModel)
            .filter(AttendanceCodeIssueModel.campaign_id == campaign.id)
            .order_by(AttendanceCodeIssueModel.id.desc()).first())
        active = (campaign.attendance_code is not None
            and campaign.attendance_code_expires_at is not None
            and now < campaign.attendance_code_expires_at)
        if campaign.attendance_code_type == "CHECK_OUT":
            if data.code_type == "CHECK_OUT" and active:
                return {"code": campaign.attendance_code,
                        "expires_at": campaign.attendance_code_expires_at,
                        "code_type": "CHECK_OUT"}
            if data.code_type != "CHECK_OUT":
                raise HTTPException(409, "Đã phát mã CHECK-OUT; không thể quay lại phát mã CHECK-IN")
        if active:
            if campaign.attendance_code_type == data.code_type:
                return {"code": campaign.attendance_code,
                        "expires_at": campaign.attendance_code_expires_at,
                        "code_type": data.code_type}
            # Cho phép Organizer phát mã CHECK-OUT bất cứ lúc nào khi cần,
            # tự động thu hồi mã CHECK-IN đang hiệu lực trước đó.
            if data.code_type == "CHECK_OUT":
                db.query(AttendanceCodeIssueModel).filter(
                    AttendanceCodeIssueModel.campaign_id == campaign.id,
                    AttendanceCodeIssueModel.code_type == "CHECK_IN",
                    AttendanceCodeIssueModel.revoked_at.is_(None),
                ).update({AttendanceCodeIssueModel.revoked_at: now}, synchronize_session=False)
            else:
                raise HTTPException(409, "Mã CHECK-IN đang hiệu lực; chờ hết hạn trước khi phát CHECK-OUT")
        code = generate_code()
        while (db.query(CampaignModel).filter(
            CampaignModel.attendance_code == code, CampaignModel.id != campaign.id
        ).first() is not None or db.query(AttendanceCodeIssueModel.id).filter(
            AttendanceCodeIssueModel.code == code,
            AttendanceCodeIssueModel.expires_at > now,
            AttendanceCodeIssueModel.revoked_at.is_(None),
        ).first() is not None):
            code = generate_code()

        expires_at = min(now + timedelta(minutes=data.expires_minutes), campaign.end_time)
        campaign.attendance_code = code
        campaign.attendance_code_expires_at = expires_at
        campaign.attendance_code_type = data.code_type
        db.add(AttendanceCodeIssueModel(
            campaign_id=campaign.id, issued_by=current_user.id, code=code,
            code_type=data.code_type, issued_at=now, expires_at=expires_at,
        ))

        db.commit()

        return {
            "code": code,
            "expires_at": expires_at,
            "code_type": data.code_type
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

        validate_code(campaign, data.code, now, "CHECK_IN")

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

        validate_code(campaign, data.code, now, "CHECK_OUT")

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


def ensure_attendance_editable(db: Session, registration: RegistrationModel):
    verified_claim = db.query(HourClaimModel.id).filter(
        HourClaimModel.registration_id == registration.id,
        HourClaimModel.status == "VERIFIED",
    ).first()
    if verified_claim is not None:
        raise HTTPException(
            status_code=409,
            detail="Đã xác minh giờ đóng góp; không thể chỉnh sửa trực tiếp điểm danh",
        )
    active_cert = db.query(CertificateModel.id).filter(
        CertificateModel.campaign_id == registration.campaign_id,
        CertificateModel.user_id == registration.user_id,
        CertificateModel.status == "ACTIVE",
    ).first()
    if active_cert is not None:
        raise HTTPException(
            status_code=409,
            detail="Đã cấp chứng nhận cho tình nguyện viên; không thể chỉnh sửa trực tiếp điểm danh",
        )


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

def _clamp_time_to_campaign(now: datetime, campaign: CampaignModel) -> datetime:
    if campaign.start_time and now < campaign.start_time:
        return campaign.start_time
    if campaign.end_time and now > campaign.end_time:
        return campaign.end_time
    return now


def manual_attendance(db, campaign_id, data, current_user):
    try:
        campaign = check_organizer_campaign(
            db, campaign_id, current_user
        )
        now = now_vietnam()
        if campaign.status in ("CANCELLED", "DRAFT", "PENDING"):
            raise HTTPException(400, "Chiến dịch không cho phép điểm danh")
        if campaign.start_time and now < campaign.start_time:
            raise HTTPException(400, "Chiến dịch chưa bắt đầu")

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

        default_checkin = _clamp_time_to_campaign(now, campaign)

        attendance = AttendanceModel(
            registration_id=registration.id,
            status=data.status,
            check_in_at=default_checkin if data.status == "PRESENT" else None,
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

        campaign = check_organizer_campaign(
            db, registration.campaign_id, current_user
        )
        ensure_attendance_editable(db, registration)

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
                attendance.check_in_at = _clamp_time_to_campaign(now, campaign)

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

        campaign = check_organizer_campaign(
            db, registration.campaign_id, current_user
        )
        ensure_attendance_editable(db, registration)

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

        if check_in is not None and (check_in < campaign.start_time or check_in > campaign.end_time):
            raise HTTPException(
                status_code=422,
                detail="Giờ check-in phải nằm trong khoảng thời gian diễn ra chiến dịch"
            )

        if check_out is not None and check_out > campaign.end_time:
            raise HTTPException(
                status_code=422,
                detail="Giờ check-out không được vượt quá thời gian kết thúc chiến dịch"
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

def get_attendance_code_history(db, campaign_id, current_user):
    check_organizer_campaign(db, campaign_id, current_user)
    campaign = get_campaign(db, campaign_id)
    now = now_vietnam()
    issues = (db.query(AttendanceCodeIssueModel)
        .filter(AttendanceCodeIssueModel.campaign_id == campaign_id)
        .order_by(AttendanceCodeIssueModel.id.desc()).limit(100).all())
    return [{"id": issue.id, "code": issue.code,
             "code_type": issue.code_type, "issued_by": issue.issued_by,
             "issued_at": issue.issued_at, "expires_at": issue.expires_at,
             "is_current": issue.code == campaign.attendance_code and issue.code_type == campaign.attendance_code_type,
             "is_active": (issue.code == campaign.attendance_code and
                issue.code_type == campaign.attendance_code_type and
                now < issue.expires_at and campaign.status in ("OPEN", "CLOSED")),
             } for issue in issues]


def get_current_attendance_code(db, campaign_id, current_user):
    check_organizer_campaign(db, campaign_id, current_user)
    campaign = get_campaign(db, campaign_id)
    if not campaign.attendance_code:
        return None
    return {"code": campaign.attendance_code,
            "code_type": campaign.attendance_code_type,
            "expires_at": campaign.attendance_code_expires_at,
            "is_active": campaign.attendance_code_expires_at is not None and
                now_vietnam() < campaign.attendance_code_expires_at and
                campaign.status in ("OPEN", "CLOSED")}
