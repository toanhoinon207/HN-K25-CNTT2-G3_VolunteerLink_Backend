from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AttendanceBase(BaseModel):
    check_in_at: Optional[datetime] = None
    check_out_at: Optional[datetime] = None
    total_minutes: int = 0
    recorded_by: Optional[int] = None


class AttendanceCreate(AttendanceBase):
    registration_id: int


class AttendanceUpdate(BaseModel):
    check_in_at: Optional[datetime] = None
    check_out_at: Optional[datetime] = None
    total_minutes: Optional[int] = None
    recorded_by: Optional[int] = None


class AttendanceResponse(AttendanceBase):
    id: int
    registration_id: int
    model_config = ConfigDict(from_attributes=True)