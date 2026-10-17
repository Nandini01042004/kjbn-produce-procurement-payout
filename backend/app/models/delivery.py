from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from app.clock import get_current_time


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False, index=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False, index=True)
    grade = Column(String(20), nullable=False)
    gross_weight_kg = Column(Numeric(12, 2), nullable=False)
    moisture = Column(Numeric(5, 2), nullable=False)
    delivered_on = Column(DateTime(timezone=True), nullable=False, index=True)

    # Computed breakdown frozen at the time of entry (Rule 3)
    gross_kg = Column(Numeric(12, 2), nullable=False)
    deduction_pct = Column(Numeric(5, 2), nullable=False)
    deduction_kg = Column(Numeric(12, 2), nullable=False)
    net_kg = Column(Numeric(12, 2), nullable=False)
    applied_price = Column(Numeric(10, 2), nullable=False)
    applied_price_list_id = Column(Integer, ForeignKey("price_lists.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)

    # Payout linking (Rule 4, Rule 6)
    payout_id = Column(Integer, ForeignKey("payouts.id"), nullable=True, index=True)

    # Credit/debit note correction support (Rule 6)
    reference_delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=True)
    is_credit_debit_note = Column(Boolean, nullable=False, default=False)
    note_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=get_current_time)

    # Relationships
    farmer = relationship("Farmer", back_populates="deliveries")
    crop = relationship("Crop", back_populates="deliveries")
    applied_price_list = relationship("PriceList", back_populates="deliveries")
    payout = relationship("Payout", back_populates="deliveries")
    referenced_delivery = relationship("Delivery", remote_side=[id], backref="adjustments")
