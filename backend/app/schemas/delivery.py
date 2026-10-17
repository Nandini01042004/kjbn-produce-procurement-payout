from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class DeliveryPreviewRequest(BaseModel):
    crop_id: int
    grade: str = Field(..., min_length=1, max_length=20)
    gross_weight_kg: Decimal = Field(...)
    moisture: Decimal = Field(...)
    delivered_on: datetime = Field(...)


class DeliveryBreakdown(BaseModel):
    gross_kg: Decimal
    deduction_pct: Decimal
    deduction_kg: Decimal
    net_kg: Decimal
    applied_price: Decimal
    applied_price_list_id: int
    amount: Decimal


class DeliveryPreviewResponse(BaseModel):
    crop_id: int
    crop_name: str
    grade: str
    gross_weight_kg: Decimal
    moisture: Decimal
    delivered_on: datetime
    breakdown: DeliveryBreakdown


class DeliveryCreate(DeliveryPreviewRequest):
    farmer_id: int
    reference_delivery_id: Optional[int] = None
    is_credit_debit_note: Optional[bool] = False
    note_reason: Optional[str] = None


class DeliveryResponse(BaseModel):
    id: int
    farmer_id: int
    farmer_name: Optional[str] = None
    crop_id: int
    crop_name: Optional[str] = None
    grade: str
    gross_weight_kg: Decimal
    moisture: Decimal
    delivered_on: datetime
    gross_kg: Decimal
    deduction_pct: Decimal
    deduction_kg: Decimal
    net_kg: Decimal
    applied_price: Decimal
    applied_price_list_id: int
    amount: Decimal
    payout_id: Optional[int] = None
    reference_delivery_id: Optional[int] = None
    is_credit_debit_note: bool
    note_reason: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
