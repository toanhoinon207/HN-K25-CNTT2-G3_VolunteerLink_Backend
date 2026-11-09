import enum
from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime


class OrganizationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class OrganizationTable(Base):
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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

   
    owner = relationship("User", back_populates="organizations")
    campaigns = relationship("Campaign", back_populates="organization", cascade="all, delete-orphan")