
from sqlalchemy.orm import Session
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
