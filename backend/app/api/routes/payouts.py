from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Payout, Farmer
from app.schemas.payout import PayoutGenerateRequest, PayoutResponse
from app.schemas.delivery import DeliveryResponse
from app.domain.services import PayoutService
from app.domain.errors import EntityNotFoundError

router = APIRouter(prefix="/payouts", tags=["Payouts"])


def _build_payout_response(payout: Payout) -> PayoutResponse:
    deliveries_resp = []
    for d in payout.deliveries:
        deliveries_resp.append(
            DeliveryResponse(
                id=d.id,
                farmer_id=d.farmer_id,
                farmer_name=d.farmer.name if d.farmer else None,
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

    return PayoutResponse(
        id=payout.id,
        farmer_id=payout.farmer_id,
        farmer_name=payout.farmer.name if payout.farmer else None,
        farmer_phone=payout.farmer.phone if payout.farmer else None,
        farmer_village=payout.farmer.village if payout.farmer else None,
        farmer_bank_ref=payout.farmer.bank_reference if payout.farmer else None,
        week_start=payout.week_start,
        week_end=payout.week_end,
        gross_amount=payout.gross_amount,
        advance_deduction=payout.advance_deduction,
        net_amount=payout.net_amount,
        status=payout.status,
        finalised_at=payout.finalised_at,
        paid_at=payout.paid_at,
        created_at=payout.created_at,
        deliveries=deliveries_resp,
    )


@router.post("/generate", response_model=PayoutResponse, status_code=status.HTTP_200_OK)
def generate_weekly_payout(payload: PayoutGenerateRequest, db: Session = Depends(get_db)):
    """
    Generate or recalculate a weekly draft payout for a farmer for the week enclosing `for_date`.
    Aggregates all unassigned deliveries for Monday-Sunday, calculates 30% advance recovery cap,
    and returns statement arithmetic. Does NOT reduce farmer's stored advance balance.
    """
    draft = PayoutService.generate_draft(db, payload.farmer_id, payload.for_date)
    return _build_payout_response(draft)


@router.post("/{payout_id}/finalise", response_model=PayoutResponse)
def finalise_payout(payout_id: int, db: Session = Depends(get_db)):
    """
    Finalise a draft payout.
    Atomically deducts advance_deduction from farmer's outstanding advance and locks payout.
    Once finalised, the payout and its associated deliveries become immutable.
    """
    payout = PayoutService.finalise(db, payout_id)
    return _build_payout_response(payout)


@router.post("/{payout_id}/mark-paid", response_model=PayoutResponse)
def mark_payout_paid(payout_id: int, db: Session = Depends(get_db)):
    """Mark a finalised payout as Paid after bank disbursement."""
    payout = PayoutService.mark_paid(db, payout_id)
    return _build_payout_response(payout)


@router.get("", response_model=List[PayoutResponse])
def list_payouts(
    farmer_id: Optional[int] = Query(None, description="Filter by farmer ID"),
    status: Optional[str] = Query(None, description="Filter by status (Draft, Finalised, Paid)"),
    db: Session = Depends(get_db),
):
    """List weekly payouts."""
    query = db.query(Payout).join(Farmer)
    if farmer_id:
        query = query.filter(Payout.farmer_id == farmer_id)
    if status:
        query = query.filter(Payout.status == status)

    payouts = query.order_by(Payout.week_start.desc(), Payout.id.desc()).all()
    return [_build_payout_response(p) for p in payouts]


@router.get("/{payout_id}", response_model=PayoutResponse)
def get_payout(payout_id: int, db: Session = Depends(get_db)):
    """Get single weekly payout statement with delivery arithmetic breakdown."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise EntityNotFoundError("Payout", payout_id)
    return _build_payout_response(payout)
