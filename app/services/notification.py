
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.notifications import NotificationModel
from app.services.notifications import create_notification as create_notification


# 2. Danh sách thông báo
def get_notifications(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
):
    return (
        db.query(NotificationModel)
        .filter(NotificationModel.user_id == user_id)
        .order_by(
            NotificationModel.created_at.desc(),
            NotificationModel.id.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# 3. Đếm thông báo chưa đọc
def count_unread_notifications(
    db: Session,
    user_id: int,
):
    return (
        db.query(NotificationModel)
        .filter(
            NotificationModel.user_id == user_id,
            NotificationModel.is_read.is_(False),
        )
        .count()
    )


# 4. Đánh dấu một thông báo đã đọc
def mark_notification_read(
    db: Session,
    user_id: int,
    notification_id: int,
):
    notification = (
        db.query(NotificationModel)
        .filter(
            NotificationModel.id == notification_id,
            NotificationModel.user_id == user_id,
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy thông báo",
        )

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification


# 5. Đánh dấu tất cả đã đọc
def mark_all_notifications_read(
    db: Session,
    user_id: int,
):
    updated_count = (
        db.query(NotificationModel)
        .filter(
            NotificationModel.user_id == user_id,
            NotificationModel.is_read.is_(False),
        )
        .update(
            {NotificationModel.is_read: True},
            synchronize_session=False,
        )
    )

    db.commit()

    return updated_count
