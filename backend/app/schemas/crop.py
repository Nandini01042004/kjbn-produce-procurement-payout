from datetime import datetime
from decimal import Decimal
from typing import List
from pydantic import BaseModel, Field


class CropBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Maize")
    allowed_grades: List[str] = Field(..., min_items=1, example=["A", "B", "C"])
    base_moisture_threshold: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"), example=Decimal("14.00"))
    max_moisture_accepted: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"), example=Decimal("20.00"))


class CropCreate(CropBase):
    pass


class CropResponse(CropBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
