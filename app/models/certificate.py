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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)


class CertificateModel(Base):
    __tablename__ = "certificates"

    # Mỗi tình nguyện viên chỉ có một chứng nhận
    # cho mỗi chiến dịch, kể cả khi đã thu hồi.
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "campaign_id",
            name="uq_certificate_user_campaign"
        ),
    )

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
        default=now_vietnam
    )

    status = Column(
        Enum("ACTIVE", "REVOKED"),
        default="ACTIVE",
        nullable=False
    )

    # Thông tin thu hồi
    revoked_reason = Column(
        Text,
        nullable=True
    )

    revoked_at = Column(
        DateTime,
        nullable=True
    )

    revoked_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    # Relationships
    user = relationship(
        "UserModel",
        back_populates="certificates",
        foreign_keys=[user_id]
    )

    campaign = relationship(
        "CampaignModel",
        back_populates="certificates"
    )

    # Người thực hiện thu hồi (Admin)
    revoker = relationship(
        "UserModel",
        foreign_keys=[revoked_by]
    )
