
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Trạng thái chứng nhận
class CertificateStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


# Schema cơ sở
class CertificateBase(BaseModel):
    certificate_code: str = Field(
        ...,
        max_length=50
    )

    total_hours: Decimal = Field(
        ...,
        ge=0,
        description="Tổng số giờ đóng góp đã được xác minh"
    )

    status: CertificateStatus = CertificateStatus.ACTIVE

    revoked_reason: Optional[str] = None


# Schema tạo chứng nhận (sử dụng nội bộ trong Service)
class CertificateCreate(CertificateBase):
    user_id: int
    campaign_id: int


# Schema yêu cầu thu hồi chứng nhận
class CertificateRevoke(BaseModel):
    revoked_reason: str = Field(
        ...,
        min_length=1,
        description="Lý do thu hồi chứng nhận"
    )


# Schema trả về cho Admin và người sở hữu
class CertificateResponse(CertificateBase):
    id: int
    user_id: int
    campaign_id: int

    issued_at: datetime

    revoked_at: Optional[datetime] = None
    revoked_by: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# Schema tra cứu chứng nhận công khai
class CertificatePublicResponse(BaseModel):
    certificate_code: str

    volunteer_name: str
    campaign_name: str

    total_hours: Decimal

    issued_at: datetime

    status: CertificateStatus

    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IssueCertificate(BaseModel):
    campaign_id: int = Field(gt=0)
    user_id: int = Field(gt=0)
    total_hours: Decimal = Field(gt=0, max_digits=6, decimal_places=2)


class CertificateDetails(CertificateResponse):
    campaign_title: str

    model_config = ConfigDict(
        from_attributes=True
    )

