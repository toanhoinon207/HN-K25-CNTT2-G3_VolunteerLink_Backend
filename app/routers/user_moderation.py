from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_role
from app.models.users import UserModel
from app.schemas.user_moderation import (
    UserListResponse,
    UserItemResponse,
    LockUserRequest,
    UnlockUserRequest,
    ModerationHistoryItem
)
from app.services.user_moderation import (
    list_users_service,
    lock_user_service,
    unlock_user_service,
    get_user_moderation_history_service
)


router = APIRouter(
    prefix="/admin/users",
    tags=["Admin Users"]
)


@router.get("/search", response_model=UserListResponse)
def get_users_list(
    keyword: Optional[str] = Query(None, description="Tìm theo họ tên, email hoặc SĐT"),
    role: Optional[str] = Query(None, description="Lọc theo vai trò: USER, ORGANIZER, ADMIN"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái: ACTIVE, LOCKED"),
    page: int = Query(1, ge=1, description="Số trang hiện tại"),
    page_size: int = Query(10, ge=1, le=100, description="Số bản ghi trên mỗi trang"),
    db: Session = Depends(get_db),
    current_admin: UserModel = Depends(require_role("ADMIN"))
):
    """Lấy danh sách người dùng có tìm kiếm, lọc theo vai trò/trạng thái và phân trang."""
    return list_users_service(
        db=db,
        keyword=keyword,
        role=role,
        status_filter=status,
        page=page,
        page_size=page_size
    )


@router.patch("/{user_id}/lock", response_model=UserItemResponse)
def lock_user(
    user_id: int,
    payload: LockUserRequest,
    db: Session = Depends(get_db),
    current_admin: UserModel = Depends(require_role("ADMIN"))
):
    """Khóa tài khoản kèm lý do vi phạm, thu hồi mọi phiên đăng nhập đang hoạt động."""
    return lock_user_service(
        db=db,
        user_id=user_id,
        reason=payload.reason,
        admin=current_admin
    )


@router.patch("/{user_id}/unlock", response_model=UserItemResponse)
def unlock_user(
    user_id: int,
    payload: UnlockUserRequest,
    db: Session = Depends(get_db),
    current_admin: UserModel = Depends(require_role("ADMIN"))
):
    """Mở khóa tài khoản đã bị khóa kèm ghi chú lý do."""
    return unlock_user_service(
        db=db,
        user_id=user_id,
        reason=payload.reason,
        admin=current_admin
    )


@router.get("/{user_id}/history", response_model=list[ModerationHistoryItem])
def get_user_history(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: UserModel = Depends(require_role("ADMIN"))
):
    """Xem toàn bộ lịch sử xử lý khóa / mở khóa của tài khoản."""
    return get_user_moderation_history_service(
        db=db,
        user_id=user_id
    )
