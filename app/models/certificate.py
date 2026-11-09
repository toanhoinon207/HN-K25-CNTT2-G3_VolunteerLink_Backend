from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Enum,
    Numeric,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship
from app.db.session import Base

class CertificateModel(Base):
    __tablename__ = "certificates"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    certificate_code = Column(
        String(50),
        unique=True,
        nullable=False
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    campaign_id = Column(
        BigInteger,
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
        server_default=func.now()
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