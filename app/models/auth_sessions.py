from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from app.db.session import Base


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuthSessionModel(Base):
    __tablename__ = "auth_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    refresh_token_jti = Column(String(36), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now_utc)
