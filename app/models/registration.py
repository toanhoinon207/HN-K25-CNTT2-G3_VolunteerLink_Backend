
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.session import Base
from sqlalchemy.orm import relationship


class RegistrationModel(Base):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

    status = Column(String(20), default="PENDING")

    message = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime)

    campaign = relationship('CampaignModel',back_populates="registrations") 
    user = relationship('UserModel',back_populates="registrations")
    attendance = relationship('AttendanceModel',back_populates="registration",uselist=False)
    hour_claims = relationship('HourClaimModel',back_populates="registration")