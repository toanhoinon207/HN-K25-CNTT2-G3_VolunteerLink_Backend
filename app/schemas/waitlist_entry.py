
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WaitlistEntryCreate(BaseModel):
    campaign_id: int


class WaitlistEntryResponse(BaseModel):
    id: int
    user_id: int
    campaign_id: int
    position: int
    status: str
    invited_at: Optional[datetime]
    response_deadline: Optional[datetime]

    class Config:
        from_attributes = True
