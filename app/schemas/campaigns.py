
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator


def _validate_campaign_image_url(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    cleaned = v.strip()
    if not cleaned:
        return None
    if not cleaned.startswith(("http://", "https://", "/")):
        raise ValueError("URL ảnh chiến dịch phải dùng http://, https:// hoặc đường dẫn nội bộ.")
    return cleaned


CampaignStatus = Literal[
    "DRAFT",
    "PENDING",
    "OPEN",
    "CLOSED",
    "COMPLETED",
    "CANCELLED"
]


class CampaignCreate(BaseModel):

    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    image_url: Optional[str] = Field(default=None, max_length=500)

    category: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=255)

    start_time: datetime
    end_time: datetime
    registration_deadline: datetime

    max_participants: int = Field(gt=0)
    requirements: Optional[str] = None
    estimated_hours: float = Field(gt=0)

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v: Optional[str]) -> Optional[str]:
        return _validate_campaign_image_url(v)


class CampaignUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, min_length=1)
    image_url: Optional[str] = Field(default=None, max_length=500)

    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    location: Optional[str] = Field(default=None, min_length=1, max_length=255)

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None

    max_participants: Optional[int] = Field(None, gt=0)
    requirements: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, gt=0)

    @field_validator("image_url")
    @classmethod
    def check_image_url(cls, v: Optional[str]) -> Optional[str]:
        return _validate_campaign_image_url(v)


class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus
    reason: Optional[str] = None


class CampaignResponse(BaseModel):
    id: int
    organization_id: int

    title: str
    description: str
    image_url: Optional[str]

    category: str
    location: str

    start_time: datetime
    end_time: datetime
    registration_deadline: datetime

    max_participants: int
    requirements: Optional[str]
    estimated_hours: float

    status: CampaignStatus
    reason: Optional[str]

    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def display_status(self) -> str:
        from app.services.campaigns import derive_display_status
        return derive_display_status(self.status, self.start_time, self.end_time, self.registration_deadline)

    model_config = ConfigDict(from_attributes=True)


class OrganizerCampaignResponse(CampaignResponse):
    registered_count: int = 0

class OrganizationPublicResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CampaignListItemResponse(BaseModel):
    id: int
    image_url: Optional[str] = None
    title: str
    category: str
    status: Literal["OPEN", "CLOSED", "COMPLETED"]
    description: str
    location: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    max_participants: Optional[int] = None
    organization: OrganizationPublicResponse

    model_config = ConfigDict(from_attributes=True)


class CampaignListResponse(BaseModel):
    items: list[CampaignListItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CampaignDetailResponse(BaseModel):
    id: int
    organization_id: int

    image_url: Optional[str] = None
    title: str
    description: str
    category: str
    location: str
    status: Literal["OPEN", "CLOSED", "COMPLETED"]

    start_time: datetime
    end_time: datetime
    registration_deadline: datetime

    max_participants: int
    requirements: Optional[str] = None
    estimated_hours: float

    approved_count: int
    remaining_slots: int

    organization: OrganizationPublicResponse

    model_config = ConfigDict(from_attributes=True)


class CampaignPendingItemResponse(CampaignResponse):
    organization: OrganizationPublicResponse


class AdminCampaignDetailResponse(CampaignDetailResponse):
    status: CampaignStatus
    reason: Optional[str] = None


class CampaignReviewRequest(BaseModel):
    action: Literal["APPROVE", "REJECT"]
    reason: Optional[str] = Field(default=None, max_length=1000)


class CampaignCancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)
