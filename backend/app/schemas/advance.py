from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AdvanceCreate(BaseModel):
    farmer_id: int
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    given_on: datetime
    notes: Optional[str] = Field(None, max_length=255)


class AdvanceResponse(BaseModel):
    id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    amount: Decimal
    given_on: datetime
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
