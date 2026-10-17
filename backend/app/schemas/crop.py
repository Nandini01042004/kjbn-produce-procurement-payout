from datetime import datetime
from decimal import Decimal
from typing import List
from pydantic import BaseModel, Field, ConfigDict


class CropBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    allowed_grades: List[str] = Field(..., min_length=1)
    base_moisture_threshold: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))
    max_moisture_accepted: Decimal = Field(..., ge=Decimal("0.00"), le=Decimal("100.00"))


class CropCreate(CropBase):
    pass


class CropResponse(CropBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
