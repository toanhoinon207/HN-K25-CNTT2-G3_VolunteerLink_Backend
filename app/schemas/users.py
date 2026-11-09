from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field

UserRole = Literal["USER", "ORGANIZER", "ADMIN"]
UserStatus = Literal["ACTIVE", "LOCKED"]

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=20)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    phone: str | None
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
