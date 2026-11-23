
from pathlib import Path
import uuid

from fastapi import HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.users import UserModel
from app.models.volunteer_profiles import VolunteerProfileModel
from app.models.certificate import CertificateModel
from app.models.attendances import AttendanceModel
from app.models.hourclaims import HourClaimModel
from app.models.registration import RegistrationModel
from app.models.auth_sessions import AuthSessionModel, now_utc

from app.schemas.users import (
    UserProfileUpdate,
    ChangePasswordRequest
)
from app.schemas.volunteer_profile import VolunteerProfileUpdate

from app.core.security import hash_password, verify_password


# 1. Tính tổng giờ đóng góp đã xác minh (Chứng nhận ACTIVE + HourClaim VERIFIED chưa có chứng nhận)
def get_total_hours(db: Session, user_id: int) -> float:
    # 1.1. Danh sách tất cả các chiến dịch đã từng được cấp chứng nhận (cả ACTIVE và REVOKED)
    # Nếu chứng nhận bị REVOKED thì tuyệt đối không cộng lại giờ của chiến dịch đó.
    all_cert_campaign_ids = [
        row[0] for row in db.query(CertificateModel.campaign_id).filter(
            CertificateModel.user_id == user_id
        ).all()
    ]

    # Tổng giờ từ các chứng nhận đang hợp lệ (ACTIVE)
    cert_hours = db.query(
        func.coalesce(
            func.sum(CertificateModel.total_hours), 0
        )
    ).filter(
        CertificateModel.user_id == user_id,
        CertificateModel.status == "ACTIVE"
    ).scalar()

    # 1.2. Tổng giờ từ các yêu cầu xác minh giờ đã được duyệt (VERIFIED) nhưng chưa phát hành chứng nhận
    verified_claim_query = db.query(
        func.coalesce(
            func.sum(HourClaimModel.approved_hours), 0
        )
    ).join(
        RegistrationModel, HourClaimModel.registration_id == RegistrationModel.id
    ).filter(
        RegistrationModel.user_id == user_id,
        HourClaimModel.user_id == user_id,
        HourClaimModel.status == "VERIFIED",
    )

    if all_cert_campaign_ids:
        verified_claim_query = verified_claim_query.filter(
            ~RegistrationModel.campaign_id.in_(all_cert_campaign_ids)
        )

    uncertified_verified_hours = verified_claim_query.scalar()

    total = round(float(cert_hours) + float(uncertified_verified_hours), 1)
    return float(total)


# 2. Xem hồ sơ cá nhân
def get_profile(db: Session, user: UserModel):
    profile = db.query(VolunteerProfileModel).filter(
        VolunteerProfileModel.user_id == user.id
    ).first()

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "avatar_url": user.avatar_url,
        "date_of_birth": (
            profile.date_of_birth if profile else None
        ),
        "skills": profile.skills if profile else None,
        "area": profile.area if profile else None,
        "total_hours": get_total_hours(db, user.id)
    }


# 3. Cập nhật thông tin tài khoản
def update_user_profile(
    db: Session,
    user: UserModel,
    data: UserProfileUpdate
):
    values = data.model_dump(exclude_unset=True)

    if "full_name" in values:
        name = values["full_name"]

        if name is None or not name.strip():
            raise HTTPException(
                status_code=422,
                detail="Họ tên không được để trống"
            )

        user.full_name = name.strip()

    if "phone" in values:
        user.phone = values["phone"]

    if "avatar_url" in values:
        user.avatar_url = values["avatar_url"]

    db.commit()
    db.refresh(user)

    return get_profile(db, user)


ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_AVATAR_BYTES = 2 * 1024 * 1024
AVATAR_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "avatars"


def upload_user_avatar(db: Session, user: UserModel, file: UploadFile):
    """Lưu file ảnh đại diện mới và cập nhật avatar_url cho người dùng."""
    ext = ALLOWED_AVATAR_TYPES.get((file.content_type or "").lower())
    if not ext:
        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ định dạng ảnh JPG, PNG hoặc WEBP."
        )

    content = file.file.read(MAX_AVATAR_BYTES + 1)
    if not content:
        raise HTTPException(
            status_code=400,
            detail="File ảnh rỗng."
        )
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Kích thước ảnh tối đa là 2MB."
        )

    is_valid_image = (
        (ext == ".jpg" and content.startswith(b"\xff\xd8\xff"))
        or (ext == ".png" and content.startswith(b"\x89PNG\r\n\x1a\n"))
        or (ext == ".webp" and len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP")
    )
    if not is_valid_image:
        raise HTTPException(
            status_code=400,
            detail="Nội dung file không khớp định dạng ảnh JPG, PNG hoặc WEBP."
        )

    AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"user_{user.id}_{uuid.uuid4().hex}{ext}"
    target_path = AVATAR_UPLOAD_DIR / filename
    target_path.write_bytes(content)

    old_url = user.avatar_url or ""
    if old_url.startswith("/uploads/avatars/"):
        old_file = AVATAR_UPLOAD_DIR / Path(old_url).name
        if old_file.is_file():
            old_file.unlink(missing_ok=True)

    user.avatar_url = f"/uploads/avatars/{filename}"
    db.commit()
    db.refresh(user)

    return get_profile(db, user)


# 4. Cập nhật hồ sơ tình nguyện viên
def update_volunteer_profile(
    db: Session,
    user: UserModel,
    data: VolunteerProfileUpdate
):
    if user.role not in ["USER", "ORGANIZER"]:
        raise HTTPException(
            status_code=403,
            detail="Chỉ tình nguyện viên được cập nhật thông tin này"
        )

    profile = db.query(VolunteerProfileModel).filter(
        VolunteerProfileModel.user_id == user.id
    ).first()

    if profile is None:
        profile = VolunteerProfileModel(
            user_id=user.id
        )
        db.add(profile)

    values = data.model_dump(exclude_unset=True)

    if "date_of_birth" in values:
        profile.date_of_birth = values["date_of_birth"]

    if "skills" in values:
        profile.skills = values["skills"]

    if "area" in values:
        profile.area = values["area"]

    db.commit()

    return get_profile(db, user)


# 5. Đổi mật khẩu
def change_password(
    db: Session,
    user: UserModel,
    data: ChangePasswordRequest
):
    if not verify_password(
        data.old_password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Mật khẩu cũ không chính xác"
        )

    if data.old_password == data.new_password:
        raise HTTPException(
            status_code=400,
            detail="Mật khẩu mới phải khác mật khẩu cũ"
        )

    user.password_hash = hash_password(data.new_password)

    # Thu hồi tất cả phiên đăng nhập hiện tại
    db.query(AuthSessionModel).filter(
        AuthSessionModel.user_id == user.id,
        AuthSessionModel.revoked_at.is_(None)
    ).update(
        {AuthSessionModel.revoked_at: now_utc()},
        synchronize_session=False
    )

    db.commit()

    return {
        "message": "Đổi mật khẩu thành công. Vui lòng đăng nhập lại."
    }


# 6. Xem hồ sơ công khai
def get_public_profile(db: Session, user_id: int):
    user = db.query(UserModel).filter(
        UserModel.id == user_id,
        UserModel.role.in_(["USER", "ORGANIZER"]),
        UserModel.status == "ACTIVE"
    ).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy tình nguyện viên"
        )

    profile = db.query(VolunteerProfileModel).filter(
        VolunteerProfileModel.user_id == user.id
    ).first()

    campaigns_count = db.query(func.count(RegistrationModel.id)).filter(
        RegistrationModel.user_id == user.id,
        RegistrationModel.status == "APPROVED"
    ).scalar() or 0

    certs_count = db.query(func.count(CertificateModel.id)).filter(
        CertificateModel.user_id == user.id,
        CertificateModel.status == "ACTIVE"
    ).scalar() or 0

    return {
        "id": user.id,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "skills": profile.skills if profile else None,
        "area": profile.area if profile else None,
        "total_hours": get_total_hours(db, user.id),
        "certificates_count": certs_count,
        "campaigns_count": campaigns_count
    }
