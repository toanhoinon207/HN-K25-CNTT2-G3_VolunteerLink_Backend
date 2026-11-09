import enum
from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.session import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo = None)

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
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False) 
    rejection_reason = Column(Text, nullable=True) 
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

   
    owner = relationship("User", back_populates="organizations")
    campaigns = relationship("Campaign", back_populates="organization", cascade="all, delete-orphan")