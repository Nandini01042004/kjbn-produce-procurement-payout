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
from app.domain.services import (
    DeliveryService,
    PayoutService,
    FarmerLedgerService,
)
from app.schemas.delivery import DeliveryCreate, DeliveryPreviewRequest
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
# Rule 1: Effective-dated Price Lookup & Historical Immutability
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


def test_rule_1_adding_backdated_price_entry_does_not_alter_existing_delivery(
    db_session, sample_farmer, sample_crop, sample_prices
):
    """
    Edge case: Adding a back-dated price entry after deliveries exist.
    Existing delivery's frozen applied price and amount MUST NOT change!
    """
    # Create delivery on Oct 5 with prevailing price of 24.50
    req = DeliveryCreate(
        farmer_id=sample_farmer.id,
        crop_id=sample_crop.id,
        grade="A",
        gross_weight_kg=Decimal("1000.00"),
        moisture=Decimal("14.00"),
        delivered_on=datetime(2026, 10, 5, 10, 0, tzinfo=UTC),
    )
    delivery = DeliveryService.create(db_session, req)
    assert delivery.applied_price == Decimal("24.50")
    assert delivery.amount == Decimal("24500.00")
    original_price_id = delivery.applied_price_list_id

    # Later, add a back-dated price entry effective 2026-10-02 at Rs 30.00
    new_price = PriceList(
        crop_id=sample_crop.id,
        grade="A",
        price_per_kg=Decimal("30.00"),
        effective_from=date(2026, 10, 2),
    )
    db_session.add(new_price)
    db_session.commit()

    # Re-fetch delivery: must remain frozen
    db_session.refresh(delivery)
    assert delivery.applied_price == Decimal("24.50")
    assert delivery.amount == Decimal("24500.00")
    assert delivery.applied_price_list_id == original_price_id


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


def test_rule_4_week_with_zero_deliveries(db_session, sample_farmer):
    """A week with zero deliveries generates a draft payout with 0 gross and 0 net."""
    target_date = date(2026, 10, 15)
    draft = PayoutService.generate_draft(db_session, sample_farmer.id, target_date)
    assert draft.gross_amount == Decimal("0.00")
    assert draft.advance_deduction == Decimal("0.00")
    assert draft.net_amount == Decimal("0.00")
    assert draft.status == "Draft"


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


def test_rule_5_draft_does_not_reduce_advance_until_finalised(
    db_session, sample_farmer, sample_crop, sample_prices
):
    """
    CRITICAL: Outstanding advance must NOT be reduced in Draft status.
    It is reduced ONLY when the payout is Finalised.
    """
    initial_advance = sample_farmer.outstanding_advance  # Rs 5,000.00

    # Create delivery of 1000 kg at 24.50 = Rs 24,500.00
    req = DeliveryCreate(
        farmer_id=sample_farmer.id,
        crop_id=sample_crop.id,
        grade="A",
        gross_weight_kg=Decimal("1000.00"),
        moisture=Decimal("14.00"),
        delivered_on=datetime(2026, 10, 14, 10, 0, tzinfo=UTC),
    )
    DeliveryService.create(db_session, req)

    # Generate draft payout
    draft = PayoutService.generate_draft(db_session, sample_farmer.id, date(2026, 10, 14))
    assert draft.status == "Draft"
    # Gross = 24,500. 30% = 7,350. Advance = 5,000. Deduction = 5,000. Net = 19,500.
    assert draft.gross_amount == Decimal("24500.00")
    assert draft.advance_deduction == Decimal("5000.00")
    assert draft.net_amount == Decimal("19500.00")

    # Farmer outstanding advance MUST still be Rs 5,000 in DB
    db_session.refresh(sample_farmer)
    assert sample_farmer.outstanding_advance == initial_advance

    # Now finalise the payout
    finalised = PayoutService.finalise(db_session, draft.id)
    assert finalised.status == "Finalised"

    # Farmer outstanding advance MUST now be reduced to Rs 0.00
    db_session.refresh(sample_farmer)
    assert sample_farmer.outstanding_advance == Decimal("0.00")


# ------------------------------------------------------------------------------
# Rule 6: Finalised Payout Immutability & Credit/Debit Notes
# ------------------------------------------------------------------------------
def test_rule_6_finalised_payout_cannot_be_re_finalised_or_drafted(
    db_session, sample_farmer, sample_crop, sample_prices
):
    """A finalised payout is immutable."""
    req = DeliveryCreate(
        farmer_id=sample_farmer.id,
        crop_id=sample_crop.id,
        grade="A",
        gross_weight_kg=Decimal("500.00"),
        moisture=Decimal("14.00"),
        delivered_on=datetime(2026, 10, 14, 10, 0, tzinfo=UTC),
    )
    DeliveryService.create(db_session, req)
    draft = PayoutService.generate_draft(db_session, sample_farmer.id, date(2026, 10, 14))
    PayoutService.finalise(db_session, draft.id)

    # Attempting to re-finalise must fail
    with pytest.raises(ImmutablePayoutError):
        PayoutService.finalise(db_session, draft.id)

    # Attempting to generate a new draft for the same finalized week must fail
    with pytest.raises(ImmutablePayoutError):
        PayoutService.generate_draft(db_session, sample_farmer.id, date(2026, 10, 14))


def test_rule_6_credit_debit_note_lands_in_next_payout(
    db_session, sample_farmer, sample_crop, sample_prices
):
    """
    Corrections to finalised deliveries are made by credit/debit notes
    that reference the original and land in the next payout.
    """
    # Original delivery in week Oct 5 - Oct 11
    d1 = DeliveryService.create(
        db_session,
        DeliveryCreate(
            farmer_id=sample_farmer.id,
            crop_id=sample_crop.id,
            grade="A",
            gross_weight_kg=Decimal("1000.00"),
            moisture=Decimal("14.00"),
            delivered_on=datetime(2026, 10, 6, 10, 0, tzinfo=UTC),
        ),
    )
    payout_w1 = PayoutService.generate_draft(db_session, sample_farmer.id, date(2026, 10, 6))
    PayoutService.finalise(db_session, payout_w1.id)

    # Submit credit note delivery in next week (Oct 12 - Oct 18)
    credit_note = DeliveryService.create(
        db_session,
        DeliveryCreate(
            farmer_id=sample_farmer.id,
            crop_id=sample_crop.id,
            grade="A",
            gross_weight_kg=Decimal("50.00"),  # Additional 50 kg credited
            moisture=Decimal("14.00"),
            delivered_on=datetime(2026, 10, 13, 10, 0, tzinfo=UTC),
            reference_delivery_id=d1.id,
            is_credit_debit_note=True,
            note_reason="Weighbridge calibration shortfall on delivery #1",
        ),
    )
    assert credit_note.is_credit_debit_note is True
    assert credit_note.reference_delivery_id == d1.id

    # Next week's payout picks up the credit note
    payout_w2 = PayoutService.generate_draft(db_session, sample_farmer.id, date(2026, 10, 13))
    assert payout_w2.gross_amount == credit_note.amount


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
