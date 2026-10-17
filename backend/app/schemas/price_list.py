from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class PriceListBase(BaseModel):
    crop_id: int
    grade: str = Field(..., min_length=1, max_length=20)
    price_per_kg: Decimal = Field(..., gt=Decimal("0.00"))
    effective_from: date


class PriceListCreate(PriceListBase):
    pass


class PriceListResponse(PriceListBase):
    id: int
    created_at: datetime
    crop_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
