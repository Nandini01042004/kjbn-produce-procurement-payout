from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class AdvanceCreate(BaseModel):
    farmer_id: int
    amount: Decimal = Field(..., gt=Decimal("0.00"), example=Decimal("5000.00"))
    given_on: datetime = Field(..., example="2026-10-10T09:00:00Z")
    notes: Optional[str] = Field(None, max_length=255, example="Diwali seasonal advance")


class AdvanceResponse(BaseModel):
    id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    amount: Decimal
    given_on: datetime
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
