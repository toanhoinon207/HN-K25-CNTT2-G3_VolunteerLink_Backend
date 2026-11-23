from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AttendanceAppealCreate(BaseModel):
    registration_id: int = Field(gt=0)
    reason: str = Field(min_length=10, max_length=2000)
    evidence_url: str | None = Field(default=None, max_length=500)

    @field_validator("evidence_url")
    @classmethod
    def check_evidence_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        if not cleaned.startswith(("http://", "https://")):
            raise ValueError("URL minh chứng phải bắt đầu bằng http:// hoặc https://.")
        return cleaned


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


class AttendanceAppealEscalate(BaseModel):
    escalation_reason: str = Field(min_length=10, max_length=2000)


class AttendanceAppealAdminReview(BaseModel):
    decision: Literal["ACCEPTED", "REJECTED"]
    admin_note: str = Field(min_length=3, max_length=2000)
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
    escalation_reason: str | None = None
    escalated_at: datetime | None = None
    admin_id: int | None = None
    admin_note: str | None = None
    admin_resolved_at: datetime | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
