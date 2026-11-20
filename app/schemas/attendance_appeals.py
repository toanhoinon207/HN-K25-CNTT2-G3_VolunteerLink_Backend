from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AttendanceAppealCreate(BaseModel):
    registration_id: int = Field(gt=0)
    reason: str = Field(min_length=10, max_length=2000)
    evidence_url: str | None = Field(default=None, max_length=500)


class AttendanceAppealReview(BaseModel):
    decision: Literal["ACCEPTED", "REJECTED"]
    review_note: str = Field(min_length=3, max_length=2000)
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None

    @model_validator(mode="after")
    def reject_has_no_times(self):
        if self.decision == "REJECTED" and (self.check_in_at is not None or self.check_out_at is not None):
            raise ValueError("Không được cập nhật điểm danh khi từ chối")
        return self


class AttendanceAppealResponse(BaseModel):
    id: int
    registration_id: int
    user_id: int
    reason: str
    evidence_url: str | None
    status: str
    organizer_id: int | None
    review_note: str | None
    reviewed_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
