from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

UserRole = Literal["USER", "ORGANIZER", "ADMIN"]
UserStatus = Literal["ACTIVE", "LOCKED"]

def _validate_bcrypt_bytes(v: str) -> str:
    if len(v.encode("utf-8")) > 72:
        raise ValueError("Mật khẩu không được vượt quá 72 bytes.")
    return v


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        return _validate_bcrypt_bytes(v)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    phone: str | None
    avatar_url: str | None = None
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150
    )
    phone: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=500)

    @field_validator("avatar_url")
    @classmethod
    def validate_avatar_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        if not (cleaned.startswith(("http://", "https://", "/"))):
            raise ValueError("URL ảnh đại diện phải dùng http://, https:// hoặc đường dẫn nội bộ.")
        return cleaned


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(max_length=72)
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("old_password", "new_password")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        return _validate_bcrypt_bytes(v)
