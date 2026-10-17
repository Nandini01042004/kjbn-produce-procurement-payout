from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.clock import get_current_time


class PriceList(Base):
    __tablename__ = "price_lists"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=False, index=True)
    grade = Column(String(20), nullable=False, index=True)
    price_per_kg = Column(Numeric(10, 2), nullable=False)
    effective_from = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_current_time)

    # Relationships
    crop = relationship("Crop", back_populates="price_lists")
    deliveries = relationship("Delivery", back_populates="applied_price_list")

    __table_args__ = (
        UniqueConstraint("crop_id", "grade", "effective_from", name="uq_crop_grade_effective_date"),
    )
