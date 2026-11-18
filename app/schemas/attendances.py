from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

AttendanceStatus = Literal["PRESENT", "ABSENT"] 



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



class ManualAttendanceCreate(BaseModel):
    registration_id: int
    status: AttendanceStatus


# Cập nhật trạng thái
class AttendanceStatusUpdate(BaseModel):
    status: AttendanceStatus
    reason: str = Field(min_length=1, max_length=1000)


# Cập nhật giờ
class AttendanceTimeUpdate(BaseModel):
    check_in_at: Optional[datetime] = None
    check_out_at: Optional[datetime] = None
    reason: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_at_least_one_time(self):
        if (
            self.check_in_at is None
            and self.check_out_at is None
        ):
            raise ValueError(
                "Phải cung cấp ít nhất một thời gian cần chỉnh sửa"
            )

        return self


class AttendanceResponse(BaseModel):
    id: int
    registration_id: int
    check_in_at: Optional[datetime] = None
    check_out_at: Optional[datetime] = None
    total_minutes: int
    status: AttendanceStatus
    recorded_by: Optional[int] = None
    updated_by: Optional[int] = None
    updated_at: Optional[datetime] = None
    edit_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AttendanceListItem(BaseModel):
    registration_id: int
    volunteer_id: int
    volunteer_name: str

    attendance_id: Optional[int] = None
    status: Optional[AttendanceStatus] = None
    check_in_at: Optional[datetime] = None
    check_out_at: Optional[datetime] = None
    total_minutes: int = 0

    model_config = ConfigDict(from_attributes=True)