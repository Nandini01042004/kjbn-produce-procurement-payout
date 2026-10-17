from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FarmerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    village: str = Field(..., min_length=1, max_length=100)
    bank_reference: str = Field(..., min_length=1, max_length=200)


class FarmerCreate(FarmerBase):
    outstanding_advance: Optional[Decimal] = Field(default=Decimal("0.00"), ge=Decimal("0.00"))


class FarmerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    village: Optional[str] = None
    bank_reference: Optional[str] = None


class FarmerResponse(FarmerBase):
    id: int
    outstanding_advance: Decimal
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

