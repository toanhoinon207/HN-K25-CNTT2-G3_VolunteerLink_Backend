from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_role
from app.models.auth_sessions import AuthSessionModel, now_utc
from app.models.campaigns import CampaignModel
from app.models.certificate import CertificateModel
from app.models.organizations import OrganizationModel, OrganizationStatus
from app.models.user_moderation import UserModerationHistoryModel
from app.models.users import UserModel
from app.schemas.users import UserResponse
from app.services.certificates import revoke_certificate as revoke_certificate_service
from app.services.admin_dashboard import AdminDashboardService
from app.services.notifications import create_notification
from app.services.user_moderation import lock_user_service, unlock_user_service

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

    if user.role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể thay đổi trạng thái khóa của Quản trị viên khác.",
        )

    if payload.status == "LOCKED":
        if user.status != "LOCKED":
            lock_user_service(
                db=db,
                user_id=user.id,
                reason="Khóa tài khoản bởi Quản trị viên",
                admin=current_user,
            )
    elif user.status == "LOCKED":
        unlock_user_service(
            db=db,
            user_id=user.id,
            reason="Mở khóa tài khoản bởi Quản trị viên",
            admin=current_user,
        )
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
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng.",
        )

    if user.role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể thay đổi vai trò của Quản trị viên khác.",
        )

    if payload.role == "ORGANIZER" and user.role != "ORGANIZER":
        approved_org = (
            db.query(OrganizationModel)
            .filter(
                OrganizationModel.owner_id == user.id,
                OrganizationModel.status == OrganizationStatus.APPROVED,
            )
            .first()
        )
        if approved_org is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không thể gán vai trò ORGANIZER khi tài khoản chưa có hồ sơ tổ chức được phê duyệt.",
            )

    if user.role != payload.role:
        user.role = payload.role
        db.query(AuthSessionModel).filter(
            AuthSessionModel.user_id == user.id,
            AuthSessionModel.revoked_at.is_(None),
        ).update({AuthSessionModel.revoked_at: now_utc()}, synchronize_session=False)
        create_notification(
            db=db,
            user_id=user.id,
            title="Vai trò tài khoản đã được cập nhật",
            content=f"Vai trò tài khoản của bạn đã được Quản trị viên cập nhật thành {payload.role}.",
            link=None,
        )
    db.commit()
    db.refresh(user)
    return user


@router.get("/certificates")
def list_all_certificates(
    cert_status: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    """Lấy toàn bộ danh sách chứng chỉ đã cấp trong hệ thống."""
    query = (
        db.query(
            CertificateModel,
            UserModel.full_name.label("user_name"),
            UserModel.email.label("user_email"),
            CampaignModel.title.label("campaign_title"),
        )
        .join(UserModel, UserModel.id == CertificateModel.user_id)
        .join(CampaignModel, CampaignModel.id == CertificateModel.campaign_id)
    )
    if cert_status and cert_status.upper() in {"ACTIVE", "REVOKED"}:
        query = query.filter(CertificateModel.status == cert_status.upper())

    rows = query.order_by(CertificateModel.id.desc()).all()
    return [
        {
            "id": cert.id,
            "certificate_code": cert.certificate_code,
            "user_id": cert.user_id,
            "user_name": user_name,
            "user_email": user_email,
            "campaign_id": cert.campaign_id,
            "campaign_title": campaign_title,
            "total_hours": float(cert.total_hours),
            "issued_at": cert.issued_at,
            "status": cert.status,
            "revoked_reason": cert.revoked_reason,
        }
        for cert, user_name, user_email, campaign_title in rows
    ]


@router.patch("/certificates/{cert_id}/revoke")
def revoke_certificate(
    cert_id: int,
    payload: AdminCertificateRevokeRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    """Thu hồi chứng chỉ tình nguyện viên kèm lý do."""
    try:
        cert = revoke_certificate_service(
            db=db, certificate_id=cert_id, admin_id=current_user.id,
            reason=payload.reason,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "id": cert.id,
        "certificate_code": cert.certificate_code,
        "status": cert.status,
        "revoked_reason": cert.revoked_reason,
    }


@router.get("/dashboard/stats")
def get_admin_dashboard_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_role("ADMIN")),
):
    """Thống kê Dashboard cho quản trị viên."""
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ngày bắt đầu không được sau ngày kết thúc.",
        )

    stats = AdminDashboardService.get_admin_dashboard_stats(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )
    return {"message": "Thành công", "data": stats}
