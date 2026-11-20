from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_role
from app.models.campaigns import CampaignModel
from app.models.certificate import CertificateModel
from app.models.users import UserModel
from app.schemas.users import UserResponse
from app.services.notifications import create_notification
from app.services.admin import AdminDashboardService

router = APIRouter(prefix="/admin", tags=["Admin Management"])


class AdminUserStatusUpdate(BaseModel):
    status: Literal["ACTIVE", "LOCKED"]


class AdminUserRoleUpdate(BaseModel):
    role: Literal["USER", "ORGANIZER", "ADMIN"]


class AdminCertificateRevokeRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=1000)


@router.get("/users", response_model=list[UserResponse])
def list_users(
    role: Optional[str] = Query(default=None),
    user_status: Optional[str] = Query(default=None, alias="status"),
    q: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    """Lấy danh sách tài khoản người dùng cho Quản trị viên."""
    query = db.query(UserModel)
    if role and role.upper() in {"USER", "ORGANIZER", "ADMIN"}:
        query = query.filter(UserModel.role == role.upper())
    if user_status and user_status.upper() in {"ACTIVE", "LOCKED"}:
        query = query.filter(UserModel.status == user_status.upper())
    if q and q.strip():
        kw = f"%{q.strip()}%"
        query = query.filter(
            or_(UserModel.full_name.ilike(kw), UserModel.email.ilike(kw))
        )
    return query.order_by(UserModel.id.desc()).all()


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    payload: AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    """Khóa hoặc mở khóa tài khoản người dùng."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự thay đổi trạng thái khóa của chính mình.",
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng.",
        )

    user.status = payload.status
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: AdminUserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    """Cập nhật vai trò tài khoản người dùng."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự thay đổi vai trò của chính mình.",
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()