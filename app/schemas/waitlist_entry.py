from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class WaitlistEntryCreate(BaseModel):
    campaign_id: int

class WaitlistEntryResponse(BaseModel):
    id: int
    user_id: int
    campaign_id: int
    position: int
    queue_position: Optional[int] = None
    campaign_title: Optional[str] = None
    user_name: Optional[str] = None
    status: str
    invited_at: Optional[datetime]
    response_deadline: Optional[datetime]
    responded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class WaitlistResponseRequest(BaseModel):
    response: str
