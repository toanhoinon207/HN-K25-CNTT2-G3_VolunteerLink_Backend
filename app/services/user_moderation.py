import math
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models.users import UserModel
from app.models.user_moderation import UserModerationHistoryModel
from app.models.auth_sessions import AuthSessionModel, now_utc
from app.schemas.user_moderation import (
    UserItemResponse,
    UserListResponse,
    ModerationHistoryItem
)


def list_users_service(
    db: Session,
    keyword: Optional[str] = None,
    role: Optional[str] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
) -> UserListResponse:
    query = db.query(UserModel)

    # 1. Tìm kiếm theo họ tên, email, số điện thoại
    if keyword and keyword.strip():
        kw = f"%{keyword.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(UserModel.full_name).like(kw),
                func.lower(UserModel.email).like(kw),
                UserModel.phone.like(kw)
            )
        )

    # 2. Lọc theo vai trò (USER, ORGANIZER, ADMIN)
    if role and role.strip() and role.strip().upper() != "ALL":
        query = query.filter(UserModel.role == role.strip().upper())

    # 3. Lọc theo trạng thái (ACTIVE, LOCKED)
    if status_filter and status_filter.strip() and status_filter.strip().upper() != "ALL":
        query = query.filter(UserModel.status == status_filter.strip().upper())

    # 4. Phân trang
    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    safe_page = min(max(1, page), total_pages) if total > 0 else 1

    users = query.order_by(UserModel.id.desc()).offset((safe_page - 1) * page_size).limit(page_size).all()

    # 5. Tra cứu lý do khóa gần nhất cho các tài khoản đang LOCKED
    locked_user_ids = [u.id for u in users if u.status == "LOCKED"]
    lock_reasons = {}
    if locked_user_ids:
        logs = db.query(UserModerationHistoryModel).filter(
            UserModerationHistoryModel.user_id.in_(locked_user_ids),
            UserModerationHistoryModel.action == "LOCK"
        ).order_by(UserModerationHistoryModel.id.desc()).all()
        for log in logs:
            if log.user_id not in lock_reasons:
                lock_reasons[log.user_id] = log.reason

    items = [
        UserItemResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            phone=u.phone,
            avatar_url=u.avatar_url,
            role=u.role,
            status=u.status,
            created_at=u.created_at,
            updated_at=u.updated_at,
            lock_reason=lock_reasons.get(u.id)
        )
        for u in users
    ]

    return UserListResponse(
        items=items,
        total=total,
        page=safe_page,
        page_size=page_size,
        total_pages=total_pages
    )


def lock_user_service(
    db: Session,
    user_id: int,
    reason: str,
    admin: UserModel
) -> UserItemResponse:
    if not reason or not reason.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Vui lòng cung cấp lý do vi phạm khi khóa tài khoản"
        )

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng"
        )

    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự khóa tài khoản của chính mình"
        )

    if user.role == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể khóa tài khoản của Quản trị viên cấp cao"
        )

    if user.status == "LOCKED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản này hiện đang bị khóa"
        )

    clean_reason = reason.strip()

    # Cập nhật trạng thái
    user.status = "LOCKED"

    # Thu hồi toàn bộ phiên đăng nhập hiện tại để buộc đăng xuất ngay lập tức
    db.query(AuthSessionModel).filter(
        AuthSessionModel.user_id == user.id,
        AuthSessionModel.revoked_at.is_(None)
    ).update(
        {AuthSessionModel.revoked_at: now_utc()},
        synchronize_session=False
    )

    # Ghi nhận vào lịch sử xử lý
    log = UserModerationHistoryModel(
        user_id=user.id,
        admin_id=admin.id,
        action="LOCK",
        reason=clean_reason
    )
    db.add(log)
    db.commit()
    db.refresh(user)

    return UserItemResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        lock_reason=clean_reason
    )


def unlock_user_service(
    db: Session,
    user_id: int,
    reason: Optional[str],
    admin: UserModel
) -> UserItemResponse:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng"
        )

    if user.status == "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản này đang hoạt động bình thường"
        )

    if reason is not None and not reason.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Vui lòng cung cấp lý do hợp lệ khi mở khóa tài khoản"
        )

    clean_reason = reason.strip() if reason is not None else "Mở khóa tài khoản sau khi xem xét"

    # Cập nhật trạng thái
    user.status = "ACTIVE"

    # Ghi nhận vào lịch sử xử lý
    log = UserModerationHistoryModel(
        user_id=user.id,
        admin_id=admin.id,
        action="UNLOCK",
        reason=clean_reason
    )
    db.add(log)
    db.commit()
    db.refresh(user)

    return UserItemResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        lock_reason=None
    )


def get_user_moderation_history_service(
    db: Session,
    user_id: int
) -> list[ModerationHistoryItem]:
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy người dùng"
        )

    logs = db.query(UserModerationHistoryModel).filter(
        UserModerationHistoryModel.user_id == user_id
    ).order_by(UserModerationHistoryModel.id.desc()).all()

    items = []
    for log in logs:
        admin_user = log.admin
        items.append(
            ModerationHistoryItem(
                id=log.id,
                user_id=log.user_id,
                admin_id=log.admin_id,
                admin_name=admin_user.full_name if admin_user else "Hệ thống",
                admin_email=admin_user.email if admin_user else None,
                action=log.action,
                reason=log.reason,
                created_at=log.created_at
            )
        )

    return items
