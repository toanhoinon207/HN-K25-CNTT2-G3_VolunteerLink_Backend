from datetime import datetime, timezone
from sqlalchemy import (Column, Integer, String, Text, DateTime, Float, ForeignKey, Enum)
from sqlalchemy.orm import relationship
from app.db.session import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class CampaignModel(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    category = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    registration_deadline = Column(DateTime, nullable=False)
    max_participants = Column(Integer, nullable=False)
    requirements = Column(Text, nullable=True)
    estimated_hours = Column(Float, nullable=False)
    status = Column(Enum("DRAFT", "PENDING", "OPEN", "CLOSED", "COMPLETED", "CANCELLED", name="campaign_status"),nullable=False,default="DRAFT")
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    certificates = relationship("CertificateModel", back_populates="campaign")
    waitlist_entries = relationship("WaitlistEntryModel", back_populates="campaign")
    organization = relationship("OrganizationModel", back_populates="campaigns") 
    registrations = relationship("RegistrationModel", back_populates="campaign")