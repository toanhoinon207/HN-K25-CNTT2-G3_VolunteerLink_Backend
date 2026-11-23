from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.session import Base


def vietnam_now():
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).replace(tzinfo=None)


class AttendanceAppealModel(Base):
    __tablename__ = "attendance_appeals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registration_id = Column(Integer, ForeignKey("registrations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    evidence_url = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_note = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    escalation_reason = Column(Text, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_note = Column(Text, nullable=True)
    admin_resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=vietnam_now)
