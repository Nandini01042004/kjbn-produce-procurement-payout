"""
Pure Business Rules Engine for Problem 4: Produce Procurement & Payout
Enforces all core business logic (Rules 1 - 7) with pure Python and Decimal arithmetic.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from app.models import Crop, PriceList
from app.schemas.delivery import DeliveryBreakdown
from app.domain.errors import (
    MissingPriceListError,
    MoistureExceededError,
    InvalidGradeError,
    NegativeValueError,
    FutureDateError,
)

TWOPLACES = Decimal("0.01")
HUNDRED = Decimal("100.00")
THIRTY_PCT = Decimal("0.30")
TEN_PCT = Decimal("10.00")
ZERO = Decimal("0.00")


# ------------------------------------------------------------------------------
# Rule 1: Effective-dated Price Lookup
# ------------------------------------------------------------------------------
def lookup_applicable_price(
    db: Session,
    crop_id: int,
    grade: str,
    delivery_date: date,
) -> PriceList:
    """
    Rule 1: The price for a delivery is the price-list entry for its crop and grade
    with the latest effective_from on or before delivered_on. If none exists, the
    delivery is rejected with a message naming the missing combination.
    """
    clean_grade = grade.strip().upper()
    entry = (
        db.query(PriceList)
        .filter(
            PriceList.crop_id == crop_id,
            PriceList.grade == clean_grade,
            PriceList.effective_from <= delivery_date,
        )
        .order_by(PriceList.effective_from.desc(), PriceList.id.desc())
        .first()
    )

    if not entry:
        crop = db.query(Crop).filter(Crop.id == crop_id).first()
        crop_name = crop.name if crop else f"ID {crop_id}"
        raise MissingPriceListError(
            crop_name=crop_name,
            grade=clean_grade,
            delivered_on=str(delivery_date),
        )

    return entry


# ------------------------------------------------------------------------------
# Rule 2: Moisture Deduction Calculation
# ------------------------------------------------------------------------------
def calculate_moisture_deduction(moisture: Decimal, crop: Crop) -> Decimal:
    """
    Rule 2: Moisture deduction: if moisture exceeds the crop's threshold, deduct 1% of
    gross weight for every full 1% above threshold, capped at 10%.
    Produce above the crop's maximum moisture is rejected.
    Example: threshold 14%, delivered at 17.6% -> 3.6% excess -> 3% deduction.
    """
    if moisture > crop.max_moisture_accepted:
        raise MoistureExceededError(
            moisture=str(moisture),
            max_accepted=str(crop.max_moisture_accepted),
            crop_name=crop.name,
        )

    if moisture <= crop.base_moisture_threshold:
        return ZERO

    excess = moisture - crop.base_moisture_threshold
    # "for every full 1% above threshold" -> integer floor of excess
    full_percent = Decimal(int(excess))
    deduction_pct = min(TEN_PCT, full_percent)
    return deduction_pct.quantize(TWOPLACES)


# ------------------------------------------------------------------------------
# Rule 3: Frozen Breakdown Calculation & Invariant Enforcement
# ------------------------------------------------------------------------------
def compute_delivery_breakdown(
    gross_kg: Decimal,
    moisture: Decimal,
    crop: Crop,
    price_entry: PriceList,
    bonus_per_kg: Decimal = ZERO,
) -> DeliveryBreakdown:
    """
    Rule 3: Every delivery stores a breakdown:
    gross kg, deduction %, deduction kg, net kg, applied price, applied price-list entry id,
    amount (net kg × price), rounded to 2 decimals half-up.
    Editing a price list later must not change existing deliveries.

    Invariant: gross_kg == net_kg + deduction_kg (net equals sum of parts).
    """
    deduction_pct = calculate_moisture_deduction(moisture, crop)
    deduction_kg = (gross_kg * deduction_pct / HUNDRED).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    # Net kg is exactly gross_kg - deduction_kg so that net_kg + deduction_kg == gross_kg
    net_kg = gross_kg - deduction_kg

    applied_price = (price_entry.price_per_kg + bonus_per_kg).quantize(TWOPLACES)
    amount = (net_kg * applied_price).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    return DeliveryBreakdown(
        gross_kg=gross_kg.quantize(TWOPLACES),
        deduction_pct=deduction_pct,
        deduction_kg=deduction_kg,
        net_kg=net_kg.quantize(TWOPLACES),
        applied_price=applied_price,
        applied_price_list_id=price_entry.id,
        amount=amount,
    )


# ------------------------------------------------------------------------------
# Rule 4: Weekly Aggregation Boundaries (Monday - Sunday)
# ------------------------------------------------------------------------------
def calculate_weekly_boundaries(for_date: date) -> Tuple[date, date]:
    """
    Rule 4: Payouts are weekly (Monday-Sunday).
    Computes the Monday and Sunday enclosing the provided date.
    """
    # weekday(): Monday is 0, Sunday is 6
    days_since_monday = for_date.weekday()
    monday = for_date - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    return monday, sunday


# ------------------------------------------------------------------------------
# Rule 5: Advance Recovery Calculation (Capped at 30% of Gross Amount)
# ------------------------------------------------------------------------------
def calculate_payout_totals(
    gross_amount: Decimal,
    outstanding_advance: Decimal,
) -> Tuple[Decimal, Decimal]:
    """
    Rule 5: Advance recovery: deduct from each payout the lesser of the outstanding
    advance and 30% of the gross amount.
    """
    max_advance_recovery = (gross_amount * THIRTY_PCT).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    advance_deduction = min(outstanding_advance, max_advance_recovery)
    net_amount = gross_amount - advance_deduction
    return advance_deduction, net_amount


# ------------------------------------------------------------------------------
# Rule 7: Delivery Validation Checks
# ------------------------------------------------------------------------------
def validate_delivery_inputs(
    crop: Crop,
    grade: str,
    gross_weight: Decimal,
    moisture: Decimal,
    delivered_on: datetime,
    current_time: datetime,
    allow_negative_weight: bool = False,  # for credit/debit adjustment notes
) -> None:
    """
    Rule 7: Grade must be one of the crop's allowed grades;
    weight and moisture must be positive; a delivery dated in the future is rejected.
    """
    clean_grade = grade.strip().upper()
    allowed_upper = [g.upper() for g in crop.allowed_grades]
    if clean_grade not in allowed_upper:
        raise InvalidGradeError(clean_grade, crop.name, crop.allowed_grades)

    if not allow_negative_weight and gross_weight <= ZERO:
        raise NegativeValueError("gross_weight_kg", str(gross_weight))

    if moisture <= ZERO:
        raise NegativeValueError("moisture", str(moisture))

    # Reject future deliveries relative to effective current time
    if delivered_on > current_time:
        raise FutureDateError(
            delivered_on=delivered_on.isoformat(),
            current_time=current_time.isoformat(),
        )

    # Check max moisture threshold
    if moisture > crop.max_moisture_accepted:
        raise MoistureExceededError(
            moisture=str(moisture),
            max_accepted=str(crop.max_moisture_accepted),
            crop_name=crop.name,
        )
