from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class AttendanceCodeCreate(BaseModel):
    campaign_id: int = Field(gt=0)
    expires_minutes: int = Field(default=15, ge=1, le=120)
    code_type: Literal["CHECK_IN", "CHECK_OUT"] = "CHECK_IN"


class AttendanceCodeResponse(BaseModel):
    code: str
    expires_at: datetime
    code_type: Literal["CHECK_IN", "CHECK_OUT"]


class AttendanceCheckRequest(BaseModel):
    campaign_id: int = Field(gt=0)
    code: str = Field(min_length=6, max_length=6) 