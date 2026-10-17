from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.delivery import DeliveryResponse
from app.schemas.advance import AdvanceResponse


class PayoutGenerateRequest(BaseModel):
    farmer_id: int
    for_date: date = Field(..., example="2026-10-15")  # Any date in the target week


class PayoutResponse(BaseModel):
    id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    farmer_phone: Optional[str] = None
    farmer_village: Optional[str] = None
    farmer_bank_ref: Optional[str] = None
    week_start: date
    week_end: date
    gross_amount: Decimal
    advance_deduction: Decimal
    net_amount: Decimal
    status: str  # Draft, Finalised, Paid
    finalised_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    deliveries: List[DeliveryResponse] = []

    class Config:
        from_attributes = True


class FarmerLedgerResponse(BaseModel):
    farmer_id: int
    name: str
    phone: str
    village: str
    bank_reference: str
    outstanding_advance: Decimal
    total_deliveries_count: int
    total_delivered_gross_kg: Decimal
    total_delivered_net_kg: Decimal
    total_gross_earnings: Decimal
    total_advance_deducted: Decimal
    total_net_paid: Decimal
    deliveries: List[DeliveryResponse]
    advances: List[AdvanceResponse]
    payouts: List[PayoutResponse]
