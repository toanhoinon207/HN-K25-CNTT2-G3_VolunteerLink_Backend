from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Enum,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)

class CertificateModel(Base):
    __tablename__ = "certificates"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    certificate_code = Column(
        String(50),
        unique=True,
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    campaign_id = Column(
        Integer,
        ForeignKey("campaigns.id"),
        nullable=False
    )

    total_hours = Column(
        Numeric(6, 2),
        nullable=False
    )

    issued_at = Column(
        DateTime,
        nullable=False,
        default = now_vietnam 
    )

    status = Column(
        Enum("ACTIVE", "REVOKED"),
        default="ACTIVE",
        nullable=False
    )

    revoked_reason = Column(
        Text,
        nullable=True
    )

    # Relationships
    user = relationship("UserModel",back_populates="certificates")

    campaign = relationship("CampaignModel",back_populates="certificates")