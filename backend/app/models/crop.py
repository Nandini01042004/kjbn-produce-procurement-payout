import json
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.clock import get_current_time


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    _allowed_grades = Column("allowed_grades", String(100), nullable=False)  # JSON or comma-separated
    base_moisture_threshold = Column(Numeric(5, 2), nullable=False)  # e.g. 14.00 (%)
    max_moisture_accepted = Column(Numeric(5, 2), nullable=False)    # e.g. 20.00 (%)
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_current_time)

    # Relationships
    price_lists = relationship("PriceList", back_populates="crop", cascade="all, delete-orphan", order_by="desc(PriceList.effective_from)")
    deliveries = relationship("Delivery", back_populates="crop")

    @property
    def allowed_grades(self) -> list[str]:
        if not self._allowed_grades:
            return []
        try:
            return json.loads(self._allowed_grades)
        except Exception:
            return [g.strip() for g in self._allowed_grades.split(",") if g.strip()]

    @allowed_grades.setter
    def allowed_grades(self, grades: list[str]) -> None:
        self._allowed_grades = json.dumps([g.strip().upper() for g in grades])
