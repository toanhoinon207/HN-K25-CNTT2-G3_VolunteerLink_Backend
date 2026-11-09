from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class NotificationCreate(BaseModel):
    user_id: int
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    link: str | None = Field(default=None, max_length=500)

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    content: str
    link: str | None
    is_read: bool
    created_at: datetime
