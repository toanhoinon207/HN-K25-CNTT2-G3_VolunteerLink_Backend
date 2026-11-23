from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
import enum


def _validate_safe_url(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    cleaned = v.strip()
    if not cleaned:
        return None
    if not cleaned.startswith(("http://", "https://", "/")):
        raise ValueError("URL phải bắt đầu bằng http://, https:// hoặc /.")
    return cleaned


class OrganizationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"



class OrganizationBase(BaseModel):
    name: str = Field(..., max_length=255, description="Tên tổ chức")
    description: Optional[str] = Field(None, description="Mô tả tổ chức")
    logo_url: Optional[str] = Field(None, max_length=500, description="Đường dẫn logo")
    address: Optional[str] = Field(None, max_length=255, description="Địa chỉ")
    email: EmailStr = Field(..., description="Email liên hệ (unique)")
    phone: str = Field(..., max_length=20, description="Số điện thoại")
    document_url: Optional[str] = Field(None, max_length=500, description="Tài liệu xác thực")

    @field_validator("logo_url", "document_url")
    @classmethod
    def check_urls(cls, v: Optional[str]) -> Optional[str]:
        return _validate_safe_url(v)

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    document_url: Optional[str] = Field(None, max_length=500)

    @field_validator("logo_url", "document_url")
    @classmethod
    def check_urls(cls, v: Optional[str]) -> Optional[str]:
        return _validate_safe_url(v)

class OrganizationStatusUpdate(BaseModel):
    status: OrganizationStatus
    rejection_reason: Optional[str] = Field(None, description="Lý do từ chối nếu status là REJECTED")

class OrganizationResponse(OrganizationBase):
    id: int
    status: OrganizationStatus
    owner_id: int
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True) 