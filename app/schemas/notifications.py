
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str = Field(validation_alias="content")
    link: str | None = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkReadResponse(BaseModel):
    message: str
