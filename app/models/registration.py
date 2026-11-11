from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from app.db.session import Base
from sqlalchemy.orm import relationship

def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)

class RegistrationModel(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable = False)
    status = Column(String(20), default="PENDING")
    message = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable = False, default = now_vietnam)
    campaign = relationship('CampaignModel',back_populates="registrations") 
    user = relationship('UserModel',back_populates="registrations")
    attendance = relationship('AttendanceModel',back_populates="registration",uselist=False)
    hour_claims = relationship('HourClaimModel',back_populates="registration")