
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.users import UserModel
from app.models.volunteer_profiles import VolunteerProfileModel
from app.models.certificate import CertificateModel
from app.models.auth_sessions import AuthSessionModel, now_utc

from app.schemas.users import (
    UserProfileUpdate,
    ChangePasswordRequest
)
from app.schemas.volunteer_profile import VolunteerProfileUpdate

from app.core.security import hash_password, verify_password


# 1. Tính tổng giờ đóng góp
def get_total_hours(db: Session, user_id: int):
    total = db.query(
        func.coalesce(
            func.sum(CertificateModel.total_hours), 0
        )
    ).filter(
        CertificateModel.user_id == user_id,
        CertificateModel.status == "ACTIVE"
    ).scalar()

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


# 4. Cập nhật hồ sơ tình nguyện viên
def update_volunteer_profile(
    db: Session,
    user: UserModel,
    data: VolunteerProfileUpdate
):
    if user.role != "USER":
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
        UserModel.role == "USER",
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

    return {
        "id": user.id,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "skills": profile.skills if profile else None,
        "area": profile.area if profile else None,
        "total_hours": get_total_hours(db, user.id)
    }
