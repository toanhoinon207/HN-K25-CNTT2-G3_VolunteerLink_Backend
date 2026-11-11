import enum
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base

def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)

class OrganizationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class OrganizationModel(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    address = Column(String(255), nullable=True)
    email = Column(String(100), nullable=False, unique=True)
    phone = Column(String(20), nullable=False)
    document_url = Column(String(500), nullable=True) 
    status = Column(SQLEnum(OrganizationStatus), default=OrganizationStatus.PENDING, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False) 
    rejection_reason = Column(Text, nullable=True) 
    created_at = Column(DateTime, default=now_vietnam)
    updated_at = Column(DateTime, default=now_vietnam, onupdate=now_vietnam)
    owner = relationship("UserModel", back_populates="organization")
    campaigns = relationship("CampaignModel", back_populates="organization", cascade="all, delete-orphan")