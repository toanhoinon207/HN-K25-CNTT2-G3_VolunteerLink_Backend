from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# Khai báo Python Enum để đồng bộ với kiểu Enum trong Database (nếu cần validate chặt chẽ)
class CertificateStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class CertificateBase(BaseModel):
    certificate_code: str = Field(..., max_length=50)
    total_hours: Decimal = Field(..., ge=0, description="Tổng số giờ, ví dụ: 120.50")
    status: CertificateStatus = CertificateStatus.ACTIVE
    revoked_reason: Optional[str] = None


class CertificateCreate(CertificateBase):
    user_id: int
    campaign_id: int


class CertificateUpdate(BaseModel):
    certificate_code: Optional[str] = Field(None, max_length=50)
    total_hours: Optional[Decimal] = Field(None, ge=0)
    status: Optional[CertificateStatus] = None
    revoked_reason: Optional[str] = None


class CertificateResponse(CertificateBase):
    id: int
    user_id: int
    campaign_id: int
    issued_at: datetime


    model_config = ConfigDict(from_attributes=True) 