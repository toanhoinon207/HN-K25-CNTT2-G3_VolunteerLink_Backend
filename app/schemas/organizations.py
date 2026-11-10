from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
import enum


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