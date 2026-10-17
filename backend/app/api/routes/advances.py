from typing import List, Optional
from datetime import timezone
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Farmer, Advance
from app.schemas.advance import AdvanceCreate, AdvanceResponse
from app.domain.errors import EntityNotFoundError, DomainError
from app.clock import get_current_time

UTC = timezone.utc
router = APIRouter(prefix="/advances", tags=["Advances"])


@router.get("", response_model=List[AdvanceResponse])
def list_advances(
    farmer_id: Optional[int] = Query(None, description="Filter by farmer ID"),
    db: Session = Depends(get_db),
):
    """List cash advances given to farmers."""
    query = db.query(Advance).join(Farmer)
    if farmer_id:
        query = query.filter(Advance.farmer_id == farmer_id)

    advances = query.order_by(Advance.given_on.desc(), Advance.id.desc()).all()
    results = []
    for a in advances:
        r = AdvanceResponse.model_validate(a)
        r.farmer_name = a.farmer.name if a.farmer else None
        results.append(r)
    return results


@router.post("", response_model=AdvanceResponse, status_code=status.HTTP_201_CREATED)
def issue_advance(payload: AdvanceCreate, db: Session = Depends(get_db)):
    """
    Issue a new cash advance to a farmer.
    Increases the farmer's outstanding advance balance immediately.
    """
    farmer = db.query(Farmer).filter(Farmer.id == payload.farmer_id).with_for_update().first()
    if not farmer:
        raise EntityNotFoundError("Farmer", payload.farmer_id)

    if payload.amount <= 0:
        raise DomainError(
            f"Advance amount must be strictly positive (> 0), got ₹{payload.amount}.",
            code="INVALID_ADVANCE_AMOUNT",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    given_on = payload.given_on
    if given_on.tzinfo is None:
        given_on = given_on.replace(tzinfo=UTC)

    now = get_current_time()
    if given_on > now:
        raise DomainError(
            f"Advance date cannot be in the future (current system time: '{now.isoformat()}').",
            code="FUTURE_DATE_REJECTED",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # 1. Increment farmer's outstanding advance
    farmer.outstanding_advance += payload.amount

    # 2. Record advance ledger entry
    advance = Advance(
        farmer_id=farmer.id,
        amount=payload.amount,
        given_on=given_on,
        notes=payload.notes.strip() if payload.notes else None,
        created_at=now,
    )
    db.add(advance)
    db.commit()
    db.refresh(advance)

    resp = AdvanceResponse.model_validate(advance)
    resp.farmer_name = farmer.name
    return resp
