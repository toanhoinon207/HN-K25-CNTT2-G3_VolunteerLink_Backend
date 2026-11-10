from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo = None)

class WaitlistEntryModel(Base):
    __tablename__ = "waitlist_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    position = Column(Integer, nullable=False)
    status = Column(String(20), default="WAITING")
    invited_at = Column(DateTime, nullable=True)
    response_deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable = False, default = utc_now)
    campaign = relationship("CampaignModel", back_populates="waitlist_entries")
    user = relationship("UserModel", back_populates="waitlist_entries")