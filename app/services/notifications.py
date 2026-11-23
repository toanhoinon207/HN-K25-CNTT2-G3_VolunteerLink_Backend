
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.notifications import NotificationModel


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    link: str | None = None,
) -> NotificationModel:
    """Add a notification to the caller's transaction."""
    notification = NotificationModel(
        user_id=user_id,
        title=title,
        content=content,
        link=link,
        is_read=False
    )

    db.add(notification)

    return notification


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


def notify_active_admins(db: Session, title: str, content: str, link: str | None = None):
    from app.models.users import UserModel
    admins = db.query(UserModel.id).filter(
        UserModel.role == "ADMIN", UserModel.status == "ACTIVE"
    ).all()
    for (admin_id,) in admins:
        create_notification(db, admin_id, title, content, link)


def notify_campaign_organizer(db: Session, campaign_id: int,
                              title: str, content: str, link: str | None = None):
    from app.models.campaigns import CampaignModel
    from app.models.organizations import OrganizationModel
    owner = (db.query(OrganizationModel.owner_id)
        .join(CampaignModel, CampaignModel.organization_id == OrganizationModel.id)
        .filter(CampaignModel.id == campaign_id).first())
    if owner:
        create_notification(db, owner[0], title, content, link)
