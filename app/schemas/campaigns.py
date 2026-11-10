
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict


CampaignStatus = Literal[
    "DRAFT",
    "PENDING",
    "OPEN",
    "CLOSED",
    "COMPLETED",
    "CANCELLED"
]


class CampaignCreate(BaseModel):
    organization_id: int = Field(gt=0)

    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    image_url: Optional[str] = None

    category: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=255)

    start_time: datetime
    end_time: datetime
    registration_deadline: datetime

    max_participants: int = Field(gt=0)
    requirements: Optional[str] = None
    estimated_hours: float = Field(gt=0)


class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

    category: Optional[str] = None
    location: Optional[str] = None

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None

    max_participants: Optional[int] = Field(None, gt=0)
    requirements: Optional[str] = None
    estimated_hours: Optional[float] = Field(None, gt=0)


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

    model_config = ConfigDict(from_attributes=True)