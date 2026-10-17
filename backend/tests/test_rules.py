"""
Comprehensive Business Rules & Boundary Tests for Problem 4
Enforces Rule 1 through Rule 7, all edge cases, and arithmetic invariants.
"""

from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
import pytest

from app.models import Farmer, Crop, PriceList, Delivery, Advance, Payout
from app.clock import set_global_clock
from app.domain.rules import (
    lookup_applicable_price,
    calculate_moisture_deduction,
    compute_delivery_breakdown,
    calculate_weekly_boundaries,
    calculate_payout_totals,
    validate_delivery_inputs,
)
from app.domain.errors import (
    MissingPriceListError,
    MoistureExceededError,
    InvalidGradeError,
    NegativeValueError,
    FutureDateError,
    ImmutablePayoutError,
)

UTC = timezone.utc


# ------------------------------------------------------------------------------
# Rule 1: Effective-dated Price Lookup
# ------------------------------------------------------------------------------
def test_rule_1_price_lookup_exact_effective_date(db_session, sample_crop, sample_prices):
    """Delivery on the exact effective_from date must pick that price entry."""
    delivery_date = date(2026, 10, 1)
    price_entry = lookup_applicable_price(db_session, sample_crop.id, "A", delivery_date)
    assert price_entry is not None
    assert price_entry.price_per_kg == Decimal("24.50")
    assert price_entry.effective_from == date(2026, 10, 1)


def test_rule_1_price_lookup_latest_on_or_before(db_session, sample_crop, sample_prices):
    """Delivery on 2026-10-15 must pick the 2026-10-01 price, not the 2026-09-01 price."""
    delivery_date = date(2026, 10, 15)
    price_entry = lookup_applicable_price(db_session, sample_crop.id, "A", delivery_date)
    assert price_entry.price_per_kg == Decimal("24.50")


def test_rule_1_price_lookup_prior_to_newer_effective_date(db_session, sample_crop, sample_prices):
    """Delivery on 2026-09-25 must pick the 2026-09-01 price."""
    delivery_date = date(2026, 9, 25)
    price_entry = lookup_applicable_price(db_session, sample_crop.id, "A", delivery_date)
    assert price_entry.price_per_kg == Decimal("22.00")


def test_rule_1_missing_price_combination_rejected(db_session, sample_crop, sample_prices):
    """Delivery dated before any effective price entry must be rejected with named combination."""
    delivery_date = date(2026, 8, 15)
    with pytest.raises(MissingPriceListError) as exc_info:
        lookup_applicable_price(db_session, sample_crop.id, "A", delivery_date)
    assert "Maize" in str(exc_info.value)
    assert "A" in str(exc_info.value)
    assert "2026-08-15" in str(exc_info.value)


# ------------------------------------------------------------------------------
# Rule 2: Moisture Deduction
# ------------------------------------------------------------------------------
def test_rule_2_moisture_at_or_below_threshold(sample_crop):
    """Moisture at or below threshold (14.0%) incurs 0% deduction."""
    assert calculate_moisture_deduction(Decimal("14.00"), sample_crop) == Decimal("0.00")
    assert calculate_moisture_deduction(Decimal("12.50"), sample_crop) == Decimal("0.00")


def test_rule_2_moisture_at_14_99_percent(sample_crop):
    """Moisture at 14.99% with threshold 14.0% has 0.99% excess -> 0 full 1% -> 0% deduction."""
    deduction = calculate_moisture_deduction(Decimal("14.99"), sample_crop)
    assert deduction == Decimal("0.00")


def test_rule_2_moisture_at_15_00_percent(sample_crop):
    """Moisture at 15.00% with threshold 14.0% has 1.00% excess -> 1 full 1% -> 1% deduction."""
    deduction = calculate_moisture_deduction(Decimal("15.00"), sample_crop)
    assert deduction == Decimal("1.00")


def test_rule_2_moisture_example_17_6_percent(sample_crop):
    """Threshold 14%, delivered at 17.6% -> 3.6% excess -> 3 full 1% -> 3% deduction."""
    deduction = calculate_moisture_deduction(Decimal("17.60"), sample_crop)
    assert deduction == Decimal("3.00")


def test_rule_2_moisture_capped_at_10_percent(db_session):
    """Excess over 10% is capped at 10% deduction."""
    crop_high = Crop(
        name="TestCrop",
        allowed_grades=["A"],
        base_moisture_threshold=Decimal("10.00"),
        max_moisture_accepted=Decimal("25.00"),
    )
    # 23% moisture - 10% threshold = 13% excess -> capped at 10%
    assert calculate_moisture_deduction(Decimal("23.00"), crop_high) == Decimal("10.00")


def test_rule_2_moisture_above_crop_max_rejected(sample_crop):
    """Moisture exceeding crop's max_moisture_accepted is rejected."""
    with pytest.raises(MoistureExceededError) as exc_info:
        calculate_moisture_deduction(Decimal("20.01"), sample_crop)
    assert "exceeds maximum accepted moisture" in str(exc_info.value)


# ------------------------------------------------------------------------------
# Rule 3: Breakdown Rounding & Invariants
# ------------------------------------------------------------------------------
def test_rule_3_breakdown_arithmetic_and_rounding(sample_crop, sample_prices):
    """Net kg + deduction kg must equal gross kg. Amount rounded half-up to 2 decimal places."""
    price = sample_prices[1]  # Rs 24.50
    # Gross 1234.56 kg, 17.6% moisture (3% deduction)
    # Deduction kg = 1234.56 * 0.03 = 37.0368 -> rounded half-up: 37.04 kg
    # Net kg = 1234.56 - 37.04 = 1197.52 kg
    # Amount = 1197.52 * 24.50 = 29339.24
    breakdown = compute_delivery_breakdown(
        gross_kg=Decimal("1234.56"),
        moisture=Decimal("17.60"),
        crop=sample_crop,
        price_entry=price,
    )
    assert breakdown.gross_kg == Decimal("1234.56")
    assert breakdown.deduction_pct == Decimal("3.00")
    assert breakdown.deduction_kg == Decimal("37.04")
    assert breakdown.net_kg == Decimal("1197.52")
    assert breakdown.gross_kg == breakdown.net_kg + breakdown.deduction_kg
    assert breakdown.applied_price == Decimal("24.50")
    assert breakdown.amount == Decimal("29339.24")


# ------------------------------------------------------------------------------
# Rule 4: Weekly Payout Boundaries (Monday - Sunday)
# ------------------------------------------------------------------------------
def test_rule_4_weekly_boundaries_monday_to_sunday():
    """Given any date within a week, start is Monday and end is Sunday."""
    # 2026-10-15 is a Thursday
    mon, sun = calculate_weekly_boundaries(date(2026, 10, 15))
    assert mon == date(2026, 10, 12)  # Monday
    assert sun == date(2026, 10, 18)  # Sunday
    assert mon.weekday() == 0
    assert sun.weekday() == 6


# ------------------------------------------------------------------------------
# Rule 5: Advance Recovery Capped at 30% of Gross Amount
# ------------------------------------------------------------------------------
def test_rule_5_advance_deduction_capped_at_30_percent():
    """Advance deduction is lesser of outstanding advance and 30% of gross amount."""
    # Case 1: Advance is Rs 10,000, Gross is Rs 20,000. 30% is Rs 6,000. Deduction = 6,000.
    gross = Decimal("20000.00")
    outstanding = Decimal("10000.00")
    advance_ded, net = calculate_payout_totals(gross, outstanding)
    assert advance_ded == Decimal("6000.00")
    assert net == Decimal("14000.00")

    # Case 2: Advance is Rs 2,000, Gross is Rs 20,000. 30% is Rs 6,000. Deduction = 2,000.
    outstanding_small = Decimal("2000.00")
    advance_ded_2, net_2 = calculate_payout_totals(gross, outstanding_small)
    assert advance_ded_2 == Decimal("2000.00")
    assert net_2 == Decimal("18000.00")


def test_rule_5_sequential_payouts_drain_advance():
    """Farmer with large advance has 30% deducted across successive payouts until cleared."""
    advance = Decimal("10000.00")
    gross_per_week = Decimal("10000.00")  # 30% is 3000.00

    # Week 1
    ded1, _ = calculate_payout_totals(gross_per_week, advance)
    assert ded1 == Decimal("3000.00")
    advance -= ded1  # 7000.00 remaining

    # Week 2
    ded2, _ = calculate_payout_totals(gross_per_week, advance)
    assert ded2 == Decimal("3000.00")
    advance -= ded2  # 4000.00 remaining

    # Week 3
    ded3, _ = calculate_payout_totals(gross_per_week, advance)
    assert ded3 == Decimal("3000.00")
    advance -= ded3  # 1000.00 remaining

    # Week 4: Remaining 1000 is less than 3000 cap -> exactly 1000 deducted
    ded4, net4 = calculate_payout_totals(gross_per_week, advance)
    assert ded4 == Decimal("1000.00")
    assert net4 == Decimal("9000.00")
    advance -= ded4
    assert advance == Decimal("0.00")


# ------------------------------------------------------------------------------
# Rule 7: Validations (Grades, Weight, Moisture, Future Date)
# ------------------------------------------------------------------------------
def test_rule_7_invalid_grade_rejected(sample_crop):
    """Grade not in allowed_grades must be rejected."""
    with pytest.raises(InvalidGradeError) as exc_info:
        validate_delivery_inputs(
            crop=sample_crop,
            grade="D",
            gross_weight=Decimal("100.00"),
            moisture=Decimal("12.00"),
            delivered_on=datetime(2026, 10, 15, tzinfo=UTC),
            current_time=datetime(2026, 10, 17, tzinfo=UTC),
        )
    assert "Invalid grade 'D'" in str(exc_info.value)


def test_rule_7_non_positive_values_rejected(sample_crop):
    """Weight and moisture must be strictly positive (> 0)."""
    with pytest.raises(NegativeValueError):
        validate_delivery_inputs(
            crop=sample_crop,
            grade="A",
            gross_weight=Decimal("0.00"),
            moisture=Decimal("12.00"),
            delivered_on=datetime(2026, 10, 15, tzinfo=UTC),
            current_time=datetime(2026, 10, 17, tzinfo=UTC),
        )

    with pytest.raises(NegativeValueError):
        validate_delivery_inputs(
            crop=sample_crop,
            grade="A",
            gross_weight=Decimal("100.00"),
            moisture=Decimal("-1.00"),
            delivered_on=datetime(2026, 10, 15, tzinfo=UTC),
            current_time=datetime(2026, 10, 17, tzinfo=UTC),
        )


def test_rule_7_future_delivery_rejected(sample_crop):
    """Delivery dated in the future must be rejected."""
    current_time = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)
    future_time = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)
    with pytest.raises(FutureDateError):
        validate_delivery_inputs(
            crop=sample_crop,
            grade="A",
            gross_weight=Decimal("100.00"),
            moisture=Decimal("12.00"),
            delivered_on=future_time,
            current_time=current_time,
        )
