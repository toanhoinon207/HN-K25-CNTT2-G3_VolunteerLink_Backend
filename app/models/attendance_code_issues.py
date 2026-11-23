from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from app.db.session import Base
from app.models.campaigns import now_vietnam


class AttendanceCodeIssueModel(Base):
    """Append-only history of issued station codes. Organizer-only retrieval."""
    __tablename__ = "attendance_code_issues"
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    issued_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String(6), nullable=False)
    code_type = Column(String(10), nullable=False)
    issued_at = Column(DateTime, nullable=False, default=now_vietnam)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    __table_args__ = (Index("ix_code_issue_campaign_type", "campaign_id", "code_type"),)
