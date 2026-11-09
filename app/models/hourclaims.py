from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    DECIMAL,
    ForeignKey
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class HourClaimModel(Base):
    __tablename__ = "hour_claims"

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

    # Relationships
    registration = relationship("RegistrationModel", back_populates="hour_claims")
    user = relationship("UserModel", back_populates="hour_claims") 

    