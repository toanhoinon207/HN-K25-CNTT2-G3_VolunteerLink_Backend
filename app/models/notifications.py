from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class NotificationModel(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey("users.id"), unique = True, nullable = False)
    date_of_birth = Column(Date, nullable = True)
    skills = Column(Text, nullable = True)
    area = Column(String(255), nullable = True)
    user = relationship("UserModel", back_populates = "notifications")