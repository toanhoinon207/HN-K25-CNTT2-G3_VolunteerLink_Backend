from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.session import Base


def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)


class UserModerationHistoryModel(Base):
    __tablename__ = "user_moderation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)  # "LOCK" hoặc "UNLOCK"
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=now_vietnam)

    user = relationship("UserModel", foreign_keys=[user_id])
    admin = relationship("UserModel", foreign_keys=[admin_id])
