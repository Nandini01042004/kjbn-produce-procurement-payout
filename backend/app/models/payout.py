from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.clock import get_current_time


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)  # Monday
    week_end = Column(Date, nullable=False, index=True)    # Sunday
    gross_amount = Column(Numeric(12, 2), nullable=False)
    advance_deduction = Column(Numeric(12, 2), nullable=False)
    net_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), nullable=False, default="Draft")  # Draft, Finalised, Paid
    finalised_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_current_time)

    # Relationships
    farmer = relationship("Farmer", back_populates="payouts")
    deliveries = relationship("Delivery", back_populates="payout", order_by="Delivery.delivered_on")
