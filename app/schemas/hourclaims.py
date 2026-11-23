from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


def _validate_evidence_url(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    cleaned = v.strip()
    if not cleaned:
        return None
    if not cleaned.startswith(("http://", "https://")):
        raise ValueError("URL minh chứng phải bắt đầu bằng http:// hoặc https://.")
    return cleaned


class HourClaimStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class AppealStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


# =====================================================
# TNV: TẠO YÊU CẦU
# =====================================================

class HourClaimCreate(BaseModel):

    registration_id: int

    claimed_hours: Optional[Decimal] = Field(
        None,
        gt=0,
        le=Decimal("9999.99"),
        description="Số giờ đề nghị. Để trống sẽ lấy số giờ thực tế."
    )

    note: Optional[str] = None

    evidence_url: Optional[str] = Field(
        None,
        max_length=500
    )

    @field_validator("evidence_url")
    @classmethod
    def check_evidence_url(cls, v: Optional[str]) -> Optional[str]:
        return _validate_evidence_url(v)


# =====================================================
# ORGANIZER: DUYỆT YÊU CẦU
# =====================================================

class HourClaimReview(BaseModel):

    status: HourClaimStatus

    approved_hours: Optional[Decimal] = Field(
        None,
        gt=0,
        le=Decimal("9999.99")
    )

    rejection_reason: Optional[str] = None


# =====================================================
# TNV: GỬI KHIẾU NẠI
# =====================================================

class HourClaimAppealCreate(BaseModel):

    appeal_reason: str = Field(
        ...,
        min_length=1
    )

    appeal_evidence_url: Optional[str] = Field(
        None,
        max_length=500
    )

    @field_validator("appeal_evidence_url")
    @classmethod
    def check_appeal_evidence_url(cls, v: Optional[str]) -> Optional[str]:
        return _validate_evidence_url(v)


# =====================================================
# ADMIN: XỬ LÝ KHIẾU NẠI
# =====================================================

class HourClaimAppealReview(BaseModel):

    appeal_status: AppealStatus

    approved_hours: Optional[Decimal] = Field(
        None,
        gt=0,
        le=Decimal("9999.99")
    )

    admin_note: Optional[str] = None


# =====================================================
# RESPONSE
# =====================================================

class HourClaimResponse(BaseModel):

    id: int
    registration_id: int
    user_id: int
    user_name: Optional[str] = None
    campaign_title: Optional[str] = None

    actual_hours: Decimal
    claimed_hours: Decimal
    approved_hours: Optional[Decimal] = None

    note: Optional[str] = None
    evidence_url: Optional[str] = None

    status: HourClaimStatus

    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    appeal_reason: Optional[str] = None
    appeal_evidence_url: Optional[str] = None
    appeal_status: Optional[AppealStatus] = None

    admin_id: Optional[int] = None
    admin_note: Optional[str] = None
    resolved_at: Optional[datetime] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    ) 