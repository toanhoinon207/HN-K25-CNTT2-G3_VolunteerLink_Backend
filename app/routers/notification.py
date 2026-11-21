
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models import UserModel

from app.schemas.notifications import (
    NotificationResponse,
    UnreadCountResponse,
    MarkReadResponse
)

from app.services.notifications import (
    get_notifications,
    count_unread_notifications,
    mark_notification_read,
    mark_all_notifications_read,
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=list[NotificationResponse],
)
def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return get_notifications(
        db,
        current_user.id,
        skip,
        limit,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
)
def unread_count(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    count = count_unread_notifications(
        db,
        current_user.id,
    )

    return {"unread_count": count}


@router.patch(
    "/read-all",
    response_model=MarkReadResponse,
)
def read_all(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    count = mark_all_notifications_read(
        db,
        current_user.id,
    )

    return {
        "message": f"Đã đánh dấu {count} thông báo là đã đọc"
    }


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def read_one(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return mark_notification_read(
        db,
        current_user.id,
        notification_id,
    )
