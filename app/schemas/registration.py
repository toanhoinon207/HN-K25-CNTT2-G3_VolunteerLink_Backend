
from pydantic import BaseModel, ConfigDict
from typing import Optional


class RegistrationCreate(BaseModel):
    campaign_id: int
    message: Optional[str] = None


class RegistrationResponse(BaseModel):
    id: int
    user_id: int
    campaign_id: int
    status: str
    message: Optional[str]
    rejection_reason: Optional[str]
    model_config = ConfigDict(from_attributes=True) 