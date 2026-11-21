
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.users import UserModel

from app.schemas.users import (
    UserProfileUpdate,
    ChangePasswordRequest
)
from app.schemas.volunteer_profile import VolunteerProfileUpdate
from app.schemas.profile import (
    ProfileResponse,
    PublicProfileResponse
)

from app.services.profile import (
    get_profile,
    update_user_profile,
    update_volunteer_profile,
    upload_user_avatar,
    change_password,
    get_public_profile
)


router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)


# 1. Xem hồ sơ cá nhân
@router.get("/me", response_model=ProfileResponse)
def my_profile(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_profile(db, current_user)


# 2. Cập nhật thông tin tài khoản
@router.patch("/me", response_model=ProfileResponse)
def edit_profile(
    data: UserProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_user_profile(db, current_user, data)


# 2.5. Tải lên ảnh đại diện
@router.post("/avatar", response_model=ProfileResponse)
def upload_avatar(
    file: UploadFile = File(...),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return upload_user_avatar(db, current_user, file)


# 3. Cập nhật hồ sơ tình nguyện viên
@router.patch("/me/volunteer", response_model=ProfileResponse)
def edit_volunteer_profile(
    data: VolunteerProfileUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_volunteer_profile(
        db,
        current_user,
        data
    )


# 4. Đổi mật khẩu
@router.post("/change-password")
def update_password(
    data: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return change_password(db, current_user, data)


# 5. Xem hồ sơ công khai
@router.get(
    "/{user_id}",
    response_model=PublicProfileResponse
)
def public_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    return get_public_profile(db, user_id)
