from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    status: str
    created_at: datetime
    updated_at: datetime
    lock_reason: Optional[str] = None


class UserListResponse(BaseModel):
    items: list[UserItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LockUserRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000, description="Lý do vi phạm dẫn đến khóa tài khoản")


class UnlockUserRequest(BaseModel):
    reason: Optional[str] = Field(default="Mở khóa tài khoản sau khi xem xét", max_length=1000, description="Lý do hoặc ghi chú mở khóa")


class ModerationHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    admin_id: Optional[int] = None
    admin_name: Optional[str] = None
    admin_email: Optional[str] = None
    action: str
    reason: str
    created_at: datetime
