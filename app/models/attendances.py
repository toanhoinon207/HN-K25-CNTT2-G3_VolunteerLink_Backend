from sqlalchemy import Column,Integer, DateTime,ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class AttendanceModel(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, autoincrement=True)
    registration_id = Column(Integer, ForeignKey("registrations.id"), nullable=False, unique=True)
    check_in_at = Column(DateTime, nullable=True)
    check_out_at = Column(DateTime, nullable=True)
    total_minutes = Column(Integer, default=0, nullable=False)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    registration = relationship( "RegistrationModel", back_populates = "attendance")
    user = relationship("UserModel", back_populates = "attendance")