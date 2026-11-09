"""Model = cấu trúc 1 bảng trong MySQL. Bảng mẫu: items.

Khi làm đề tài, copy file này để tạo bảng của nhóm (vd: Product, Order, Movie...).
"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
class OrganizationStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class OrganizationTable(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String(255), nullable=True)
    address = Column(Text, nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    document_image_url = Column(String(255), nullable=False)
    
    
    status = Column(Enum(OrganizationStatus), default=OrganizationStatus.PENDING, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    
   
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
   
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

   
    owner = relationship("User", back_populates="organizations")
    campaigns = relationship("Campaign", back_populates="organization", cascade="all, delete-orphan")