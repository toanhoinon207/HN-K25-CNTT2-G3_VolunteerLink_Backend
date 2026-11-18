from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)

class WaitlistEntryModel(Base):
    __tablename__ = "waitlist_entries"
    __table_args__ = (UniqueConstraint("user_id", "campaign_id", name="uq_waitlist_user_campaign"),)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    position = Column(Integer, nullable=False , default=0)
    status = Column(String(20), default="WAITING")
    invited_at = Column(DateTime, nullable=True)
    response_deadline = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable = False, default = now_vietnam)
    updated_at = Column(DateTime, nullable=False, default=now_vietnam, onupdate=now_vietnam)
    campaign = relationship("CampaignModel", back_populates="waitlist_entries")
    user = relationship("UserModel", back_populates="waitlist_entries")
