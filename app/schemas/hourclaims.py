from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


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
        description="Số giờ đề nghị. Để trống sẽ lấy số giờ thực tế."
    )

    note: Optional[str] = None

    evidence_url: Optional[str] = Field(
        None,
        max_length=500
    )


# =====================================================
# ORGANIZER: DUYỆT YÊU CẦU
# =====================================================

class HourClaimReview(BaseModel):

    status: HourClaimStatus

    approved_hours: Optional[Decimal] = Field(
        None,
        gt=0
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


# =====================================================
# ADMIN: XỬ LÝ KHIẾU NẠI
# =====================================================

class HourClaimAppealReview(BaseModel):

    appeal_status: AppealStatus

    approved_hours: Optional[Decimal] = Field(
        None,
        gt=0
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
    verified_at: Optional[object] = None
    rejection_reason: Optional[str] = None

    appeal_reason: Optional[str] = None
    appeal_evidence_url: Optional[str] = None
    appeal_status: Optional[AppealStatus] = None

    admin_id: Optional[int] = None
    admin_note: Optional[str] = None
    resolved_at: Optional[object] = None

    created_at: Optional[object] = None
    updated_at: Optional[object] = None

    model_config = ConfigDict(
        from_attributes=True
    ) 