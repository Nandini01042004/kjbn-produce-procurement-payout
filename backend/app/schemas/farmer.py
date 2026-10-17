from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class FarmerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Ramesh Patel")
    phone: str = Field(..., min_length=10, max_length=15, example="9876543210")
    village: str = Field(..., min_length=1, max_length=100, example="Hunsur")
    bank_reference: str = Field(..., min_length=1, max_length=200, example="SBIN0001234-9871234567")


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

    class Config:
        from_attributes = True
