from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    DECIMAL,
    ForeignKey,
    Text,
    DateTime
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def now_vietnam():
    return datetime.now(
        ZoneInfo("Asia/Ho_Chi_Minh")
    ).replace(tzinfo=None)


class HourClaimModel(Base):
    __tablename__ = "hour_claims"

    # =====================================
    # CÁC THUỘC TÍNH CŨ - GIỮ NGUYÊN
    # =====================================

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    registration_id = Column(
        Integer,
        ForeignKey("registrations.id"),
        nullable=False
    )

    claimed_hours = Column(
        DECIMAL(6, 2),
        nullable=False
    )

    evidence_url = Column(
        String(500),
        nullable=True
    )

    status = Column(
        Enum("PENDING", "VERIFIED", "REJECTED"),
        default="PENDING",
        nullable=False
    )

    verified_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    # =====================================
    # CÁC THUỘC TÍNH MỚI
    # =====================================

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    actual_hours = Column(
        DECIMAL(6, 2),
        nullable=False
    )

    approved_hours = Column(
        DECIMAL(6, 2),
        nullable=True
    )

    note = Column(
        Text,
        nullable=True
    )

    verified_at = Column(
        DateTime,
        nullable=True
    )

    rejection_reason = Column(
        Text,
        nullable=True
    )

    appeal_reason = Column(
        Text,
        nullable=True
    )

    appeal_evidence_url = Column(
        String(500),
        nullable=True
    )

    appeal_status = Column(
        Enum("PENDING", "ACCEPTED", "REJECTED"),
        nullable=True
    )

    admin_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    admin_note = Column(
        Text,
        nullable=True
    )

    resolved_at = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=now_vietnam,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=now_vietnam,
        onupdate=now_vietnam,
        nullable=False
    )

    # =====================================
    # RELATIONSHIPS
    # =====================================

    registration = relationship(
        "RegistrationModel",
        back_populates="hour_claims"
    )

    user = relationship(
        "UserModel",
        back_populates="hour_claims",
        foreign_keys=[user_id]
    )

    verifier = relationship(
        "UserModel",
        foreign_keys=[verified_by]
    )

    admin = relationship(
        "UserModel",
        foreign_keys=[admin_id]
    ) 