
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.session import Base


class WaitlistEntryModel(Base):
    __tablename__ = "waitlist_entries"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

    position = Column(Integer)

    status = Column(String(20), default="WAITING")

    invited_at = Column(DateTime, nullable=True)
    response_deadline = Column(DateTime, nullable=True)

    created_at = Column(DateTime)
