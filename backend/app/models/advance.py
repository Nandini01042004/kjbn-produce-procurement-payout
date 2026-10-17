from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.clock import get_current_time


class Advance(Base):
    __tablename__ = "advances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    given_on = Column(DateTime(timezone=True), nullable=False, index=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_current_time)

    # Relationships
    farmer = relationship("Farmer", back_populates="advances")
