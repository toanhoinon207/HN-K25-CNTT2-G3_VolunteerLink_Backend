from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class HourClaimStatus(str, PyEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class HourClaimBase(BaseModel):
    claimed_hours: Decimal = Field(..., ge=0, description="Số giờ yêu cầu, ví dụ: 4.50")
    evidence_url: Optional[str] = Field(None, max_length=500)
    status: HourClaimStatus = HourClaimStatus.PENDING


class HourClaimCreate(HourClaimBase):
    registration_id: int


class HourClaimUpdate(BaseModel):
    claimed_hours: Optional[Decimal] = Field(None, ge=0)
    evidence_url: Optional[str] = Field(None, max_length=500)
    status: Optional[HourClaimStatus] = None
    verified_by: Optional[int] = None


class HourClaimResponse(HourClaimBase):
    id: int
    registration_id: int
    verified_by: Optional[int] = None

    # Cấu hình để Pydantic đọc dữ liệu trực tiếp từ SQLAlchemy Model objects
    model_config = ConfigDict(from_attributes=True)