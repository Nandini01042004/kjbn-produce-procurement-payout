"""
Domain Services Layer for Produce Procurement & Payout
Coordinates pure business rules with persistence and transactional consistency.
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Farmer, Crop, PriceList, Delivery, Advance, Payout
from app.schemas.delivery import (
    DeliveryPreviewRequest,
    DeliveryPreviewResponse,
    DeliveryCreate,
    DeliveryResponse,
    DeliveryBreakdown,
)
from app.schemas.payout import PayoutResponse, FarmerLedgerResponse
from app.domain.rules import (
    lookup_applicable_price,
    compute_delivery_breakdown,
    calculate_weekly_boundaries,
    calculate_payout_totals,
    validate_delivery_inputs,
    calculate_moisture_deduction,
)
from app.domain.errors import (
    EntityNotFoundError,
    ImmutablePayoutError,
    ImmutableDeliveryError,
    DomainError,
)
from app.clock import get_current_time

UTC = timezone.utc
ZERO = Decimal("0.00")
TWOPLACES = Decimal("0.01")


# ------------------------------------------------------------------------------
# Delivery Service
# ------------------------------------------------------------------------------
class DeliveryService:
    @staticmethod
    def preview(db: Session, request: DeliveryPreviewRequest) -> DeliveryPreviewResponse:
        """Preview calculation for a delivery without saving it (Core feature)."""
        crop = db.query(Crop).filter(Crop.id == request.crop_id).first()
        if not crop:
            raise EntityNotFoundError("Crop", request.crop_id)

        now = get_current_time()
        delivered_on = request.delivered_on
        if delivered_on.tzinfo is None:
            delivered_on = delivered_on.replace(tzinfo=UTC)

        # Rule 7 validations
        validate_delivery_inputs(
            crop=crop,
            grade=request.grade,
            gross_weight=request.gross_weight_kg,
            moisture=request.moisture,
            delivered_on=delivered_on,
            current_time=now,
        )

        # Rule 1 price lookup
        price_entry = lookup_applicable_price(
            db=db,
            crop_id=crop.id,
            grade=request.grade,
            delivery_date=delivered_on.date(),
        )

        # Rule 2 & 3 computed breakdown
        breakdown = compute_delivery_breakdown(
            gross_kg=request.gross_weight_kg,
            moisture=request.moisture,
            crop=crop,
            price_entry=price_entry,
        )

        return DeliveryPreviewResponse(
            crop_id=crop.id,
            crop_name=crop.name,
            grade=request.grade.upper(),
            gross_weight_kg=request.gross_weight_kg,
            moisture=request.moisture,
            delivered_on=delivered_on,
            breakdown=breakdown,
        )

    @staticmethod
    def create(db: Session, request: DeliveryCreate) -> Delivery:
        """Create and freeze a new delivery (Rules 1, 2, 3, 7)."""
        farmer = db.query(Farmer).filter(Farmer.id == request.farmer_id).first()
        if not farmer:
            raise EntityNotFoundError("Farmer", request.farmer_id)

        crop = db.query(Crop).filter(Crop.id == request.crop_id).first()
        if not crop:
            raise EntityNotFoundError("Crop", request.crop_id)

        now = get_current_time()
        delivered_on = request.delivered_on
        if delivered_on.tzinfo is None:
            delivered_on = delivered_on.replace(tzinfo=UTC)

        is_note = bool(request.is_credit_debit_note)
        ref_id = request.reference_delivery_id

        # Rule 7: Validate inputs
        validate_delivery_inputs(
            crop=crop,
            grade=request.grade,
            gross_weight=request.gross_weight_kg,
            moisture=request.moisture,
            delivered_on=delivered_on,
            current_time=now,
            allow_negative_weight=is_note,
        )

        # If credit/debit note, verify original delivery exists
        if is_note and ref_id:
            orig = db.query(Delivery).filter(Delivery.id == ref_id).first()
            if not orig:
                raise EntityNotFoundError("Original Delivery", ref_id)

        # Rule 1: Find applicable price
        price_entry = lookup_applicable_price(
            db=db,
            crop_id=crop.id,
            grade=request.grade,
            delivery_date=delivered_on.date(),
        )

        # Rule 2 & 3: Compute breakdown
        breakdown = compute_delivery_breakdown(
            gross_kg=request.gross_weight_kg,
            moisture=request.moisture,
            crop=crop,
            price_entry=price_entry,
        )

        delivery = Delivery(
            farmer_id=farmer.id,
            crop_id=crop.id,
            grade=request.grade.upper(),
            gross_weight_kg=request.gross_weight_kg,
            moisture=request.moisture,
            delivered_on=delivered_on,
            gross_kg=breakdown.gross_kg,
            deduction_pct=breakdown.deduction_pct,
            deduction_kg=breakdown.deduction_kg,
            net_kg=breakdown.net_kg,
            applied_price=breakdown.applied_price,
            applied_price_list_id=breakdown.applied_price_list_id,
            amount=breakdown.amount,
            reference_delivery_id=ref_id,
            is_credit_debit_note=is_note,
            note_reason=request.note_reason,
            created_at=now,
        )

        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        return delivery


# ------------------------------------------------------------------------------
# Payout Service
# ------------------------------------------------------------------------------
class PayoutService:
    @staticmethod
    def generate_draft(db: Session, farmer_id: int, for_date: date) -> Payout:
        """
        Rule 4 & 5: Generate weekly payout draft aggregating all unassigned deliveries
        for the given week (Monday - Sunday).
        """
        farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
        if not farmer:
            raise EntityNotFoundError("Farmer", farmer_id)

        week_start, week_end = calculate_weekly_boundaries(for_date)

        # Check if a Finalised or Paid payout already exists for this week
        existing_finalised = (
            db.query(Payout)
            .filter(
                Payout.farmer_id == farmer_id,
                Payout.week_start == week_start,
                Payout.status.in_(["Finalised", "Paid"]),
            )
            .first()
        )
        if existing_finalised:
            raise ImmutablePayoutError(
                f"A {existing_finalised.status} payout (#{existing_finalised.id}) already exists "
                f"for farmer #{farmer_id} in week {week_start} to {week_end}."
            )

        # Find all unassigned deliveries of this farmer in the week
        # Filter deliveries delivered_on between week_start (00:00:00 UTC) and week_end (23:59:59.999999 UTC)
        start_dt = datetime(week_start.year, week_start.month, week_start.day, 0, 0, 0, tzinfo=UTC)
        end_dt = datetime(week_end.year, week_end.month, week_end.day, 23, 59, 59, 999999, tzinfo=UTC)

        # Check if there is an existing Draft payout for this week
        draft_payout = (
            db.query(Payout)
            .filter(
                Payout.farmer_id == farmer_id,
                Payout.week_start == week_start,
                Payout.status == "Draft",
            )
            .first()
        )

        eligible_deliveries = (
            db.query(Delivery)
            .filter(
                Delivery.farmer_id == farmer_id,
                Delivery.delivered_on >= start_dt,
                Delivery.delivered_on <= end_dt,
                (Delivery.payout_id == None) | (Delivery.payout_id == (draft_payout.id if draft_payout else -1)),
            )
            .all()
        )

        # Rule 3 & 4: gross amount is sum of delivery amounts
        gross_amount = sum((d.amount for d in eligible_deliveries), ZERO).quantize(TWOPLACES)

        # Rule 5: Calculate advance recovery (lesser of outstanding advance and 30% gross)
        advance_deduction, net_amount = calculate_payout_totals(
            gross_amount=gross_amount,
            outstanding_advance=farmer.outstanding_advance,
        )

        now = get_current_time()

        if draft_payout:
            draft_payout.gross_amount = gross_amount
            draft_payout.advance_deduction = advance_deduction
            draft_payout.net_amount = net_amount
        else:
            draft_payout = Payout(
                farmer_id=farmer.id,
                week_start=week_start,
                week_end=week_end,
                gross_amount=gross_amount,
                advance_deduction=advance_deduction,
                net_amount=net_amount,
                status="Draft",
                created_at=now,
            )
            db.add(draft_payout)
            db.flush()

        # Link eligible deliveries to this draft payout
        for d in eligible_deliveries:
            d.payout_id = draft_payout.id

        db.commit()
        db.refresh(draft_payout)
        return draft_payout

    @staticmethod
    def finalise(db: Session, payout_id: int) -> Payout:
        """
        Rule 5 & 6: Finalise payout.
        Reduces the farmer's outstanding advance accordingly ONLY when the payout is Finalised.
        Once finalised, the payout is immutable.
        """
        payout = db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            raise EntityNotFoundError("Payout", payout_id)

        if payout.status != "Draft":
            raise ImmutablePayoutError(f"Payout #{payout_id} is already {payout.status} and cannot be finalised again.")

        # Concurrency safety: Lock farmer record for update
        farmer = db.query(Farmer).filter(Farmer.id == payout.farmer_id).with_for_update().first()
        if not farmer:
            raise EntityNotFoundError("Farmer", payout.farmer_id)

        # Recalculate advance deduction against fresh farmer outstanding advance
        actual_deduction, actual_net = calculate_payout_totals(
            gross_amount=payout.gross_amount,
            outstanding_advance=farmer.outstanding_advance,
        )

        # Rule 5: Deduct advance from farmer's outstanding balance
        farmer.outstanding_advance = (farmer.outstanding_advance - actual_deduction).quantize(TWOPLACES)
        payout.advance_deduction = actual_deduction
        payout.net_amount = actual_net

        # Rule 6: Mark Finalised (immutable)
        now = get_current_time()
        payout.status = "Finalised"
        payout.finalised_at = now

        db.commit()
        db.refresh(payout)
        return payout

    @staticmethod
    def mark_paid(db: Session, payout_id: int) -> Payout:
        """Mark a finalised payout as Paid."""
        payout = db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            raise EntityNotFoundError("Payout", payout_id)

        if payout.status == "Paid":
            return payout

        if payout.status != "Finalised":
            raise DomainError(
                f"Payout #{payout_id} is in status '{payout.status}'. Only 'Finalised' payouts can be marked as Paid.",
                code="INVALID_PAYOUT_STATUS",
                status_code=400,
            )

        now = get_current_time()
        payout.status = "Paid"
        payout.paid_at = now
        db.commit()
        db.refresh(payout)
        return payout


# ------------------------------------------------------------------------------
# Farmer Ledger Service
# ------------------------------------------------------------------------------
class FarmerLedgerService:
    @staticmethod
    def get_ledger(db: Session, farmer_id: int) -> FarmerLedgerResponse:
        """Retrieve complete farmer financial ledger with chronological deliveries, advances, and payouts."""
        farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
        if not farmer:
            raise EntityNotFoundError("Farmer", farmer_id)

        deliveries = (
            db.query(Delivery)
            .filter(Delivery.farmer_id == farmer_id)
            .order_by(Delivery.delivered_on.desc())
            .all()
        )
        advances = (
            db.query(Advance)
            .filter(Advance.farmer_id == farmer_id)
            .order_by(Advance.given_on.desc())
            .all()
        )
        payouts = (
            db.query(Payout)
            .filter(Payout.farmer_id == farmer_id)
            .order_by(Payout.week_start.desc())
            .all()
        )

        # Aggregate stats
        total_deliveries_count = len(deliveries)
        total_gross_kg = sum((d.gross_kg for d in deliveries), ZERO)
        total_net_kg = sum((d.net_kg for d in deliveries), ZERO)
        total_gross_earnings = sum((d.amount for d in deliveries), ZERO)

        finalised_payouts = [p for p in payouts if p.status in ["Finalised", "Paid"]]
        total_advance_deducted = sum((p.advance_deduction for p in finalised_payouts), ZERO)
        total_net_paid = sum((p.net_amount for p in finalised_payouts if p.status == "Paid"), ZERO)

        # Map to schemas
        from app.schemas.delivery import DeliveryResponse
        from app.schemas.advance import AdvanceResponse
        from app.schemas.payout import PayoutResponse

        deliv_resps = []
        for d in deliveries:
            deliv_resps.append(
                DeliveryResponse(
                    id=d.id,
                    farmer_id=d.farmer_id,
                    farmer_name=farmer.name,
                    crop_id=d.crop_id,
                    crop_name=d.crop.name if d.crop else None,
                    grade=d.grade,
                    gross_weight_kg=d.gross_weight_kg,
                    moisture=d.moisture,
                    delivered_on=d.delivered_on,
                    gross_kg=d.gross_kg,
                    deduction_pct=d.deduction_pct,
                    deduction_kg=d.deduction_kg,
                    net_kg=d.net_kg,
                    applied_price=d.applied_price,
                    applied_price_list_id=d.applied_price_list_id,
                    amount=d.amount,
                    payout_id=d.payout_id,
                    reference_delivery_id=d.reference_delivery_id,
                    is_credit_debit_note=d.is_credit_debit_note,
                    note_reason=d.note_reason,
                    created_at=d.created_at,
                )
            )

        adv_resps = [
            AdvanceResponse(
                id=a.id,
                farmer_id=a.farmer_id,
                farmer_name=farmer.name,
                amount=a.amount,
                given_on=a.given_on,
                notes=a.notes,
                created_at=a.created_at,
            )
            for a in advances
        ]

        payout_resps = [
            PayoutResponse(
                id=p.id,
                farmer_id=p.farmer_id,
                farmer_name=farmer.name,
                farmer_phone=farmer.phone,
                farmer_village=farmer.village,
                farmer_bank_ref=farmer.bank_reference,
                week_start=p.week_start,
                week_end=p.week_end,
                gross_amount=p.gross_amount,
                advance_deduction=p.advance_deduction,
                net_amount=p.net_amount,
                status=p.status,
                finalised_at=p.finalised_at,
                paid_at=p.paid_at,
                created_at=p.created_at,
                deliveries=[],
            )
            for p in payouts
        ]

        return FarmerLedgerResponse(
            farmer_id=farmer.id,
            name=farmer.name,
            phone=farmer.phone,
            village=farmer.village,
            bank_reference=farmer.bank_reference,
            outstanding_advance=farmer.outstanding_advance,
            total_deliveries_count=total_deliveries_count,
            total_delivered_gross_kg=total_gross_kg,
            total_delivered_net_kg=total_net_kg,
            total_gross_earnings=total_gross_earnings,
            total_advance_deducted=total_advance_deducted,
            total_net_paid=total_net_paid,
            deliveries=deliv_resps,
            advances=adv_resps,
            payouts=payout_resps,
        )
