from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.clock import get_current_time


class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False, unique=True, index=True)
    village = Column(String(100), nullable=False)
    bank_reference = Column(String(200), nullable=False)
    outstanding_advance = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_current_time)

    # Relationships
    deliveries = relationship("Delivery", back_populates="farmer", order_by="desc(Delivery.delivered_on)")
    advances = relationship("Advance", back_populates="farmer", order_by="desc(Advance.given_on)")
    payouts = relationship("Payout", back_populates="farmer", order_by="desc(Payout.week_start)")
