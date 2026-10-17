from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class PriceListBase(BaseModel):
    crop_id: int
    grade: str = Field(..., min_length=1, max_length=20, example="A")
    price_per_kg: Decimal = Field(..., gt=Decimal("0.00"), example=Decimal("24.50"))
    effective_from: date = Field(..., example="2026-10-01")


class PriceListCreate(PriceListBase):
    pass


class PriceListResponse(PriceListBase):
    id: int
    created_at: datetime
    crop_name: Optional[str] = None

    class Config:
        from_attributes = True
