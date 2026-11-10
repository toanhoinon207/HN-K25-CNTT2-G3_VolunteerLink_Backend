from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo = None)

class NotificationModel(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    title = Column(String(200), nullable = False)
    content = Column(Text, nullable = False)
    link = Column(String(500))
    is_read = Column(Boolean, nullable = False, default = False)
    created_at = Column(DateTime, nullable = False, default = utc_now)
    user = relationship("UserModel", back_populates = "notifications")