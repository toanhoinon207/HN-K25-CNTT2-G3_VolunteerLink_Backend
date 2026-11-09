from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo = None)

class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True)
    email = Column(String(255), nullable = False, unique = True)
    password_hash = Column(String(255), nullable = False)
    full_name = Column(String(150), nullable = False)
    phone = Column(String(20))
    role = Column(Enum("USER", "ORGANIZER", "ADMIN"), nullable = False, default = "USER")
    status = Column(Enum("ACTIVE", "LOCKED"), nullable = False, default = "ACTIVE")
    created_at = Column(DateTime, nullable = False, default = utc_now)
    updated_at = Column(DateTime, nullable = False, default = utc_now, onupdate = utc_now)
    volunteer_profile = relationship("VolunteerProfileModel", back_populates = "user", uselist = False)
    registrations = relationship("RegistrationModel", back_populates = "user")
    notifications = relationship("NotificationModel", back_populates = "user")
    hour_claims = relationship("HourClaimModel", back_populates = "user")
    certificates = relationship("CertificateModel", back_populates = "user")