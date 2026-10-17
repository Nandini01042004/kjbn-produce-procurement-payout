from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Crop, PriceList
from app.schemas.price_list import PriceListCreate, PriceListResponse
from app.domain.errors import EntityNotFoundError, DomainError

router = APIRouter(prefix="/price-lists", tags=["Price Lists"])


@router.get("", response_model=List[PriceListResponse])
def list_price_lists(
    crop_id: Optional[int] = Query(None, description="Filter by crop ID"),
    grade: Optional[str] = Query(None, description="Filter by grade"),
    db: Session = Depends(get_db),
):
    """List price list entries with crop names and effective dates."""
    query = db.query(PriceList).join(Crop)
    if crop_id:
        query = query.filter(PriceList.crop_id == crop_id)
    if grade:
        query = query.filter(PriceList.grade == grade.strip().upper())

    entries = query.order_by(PriceList.effective_from.desc(), PriceList.id.desc()).all()
    results = []
    for e in entries:
        r = PriceListResponse.model_validate(e)
        r.crop_name = e.crop.name if e.crop else None
        results.append(r)
    return results


@router.post("", response_model=PriceListResponse, status_code=status.HTTP_201_CREATED)
def create_price_list_entry(payload: PriceListCreate, db: Session = Depends(get_db)):
    """
    Add an effective-dated price list entry.
    Rule: Price list entries are effective-dated and never overwritten.
    If an entry already exists for the exact crop, grade, and effective_from, reject.
    """
    crop = db.query(Crop).filter(Crop.id == payload.crop_id).first()
    if not crop:
        raise EntityNotFoundError("Crop", payload.crop_id)

    clean_grade = payload.grade.strip().upper()
    if clean_grade not in [g.upper() for g in crop.allowed_grades]:
        raise DomainError(
            f"Grade '{clean_grade}' is not permitted for crop '{crop.name}'. "
            f"Allowed grades are: {', '.join(crop.allowed_grades)}.",
            code="INVALID_GRADE",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Check for duplicate on the exact date
    existing = (
        db.query(PriceList)
        .filter(
            PriceList.crop_id == crop.id,
            PriceList.grade == clean_grade,
            PriceList.effective_from == payload.effective_from,
        )
        .first()
    )
    if existing:
        raise DomainError(
            f"A price list entry for {crop.name} Grade {clean_grade} on effective date "
            f"{payload.effective_from} already exists at ₹{existing.price_per_kg}/kg (Entry #{existing.id}). "
            f"Historical prices are never overwritten; choose an appropriate effective date.",
            code="PRICE_ENTRY_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT,
        )

    entry = PriceList(
        crop_id=crop.id,
        grade=clean_grade,
        price_per_kg=payload.price_per_kg,
        effective_from=payload.effective_from,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    resp = PriceListResponse.model_validate(entry)
    resp.crop_name = crop.name
    return resp


@router.get("/history", response_model=List[PriceListResponse])
def get_price_history(crop_id: int, grade: str, db: Session = Depends(get_db)):
    """Retrieve full chronological pricing history for a specific crop and grade."""
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise EntityNotFoundError("Crop", crop_id)

    clean_grade = grade.strip().upper()
    entries = (
        db.query(PriceList)
        .filter(PriceList.crop_id == crop_id, PriceList.grade == clean_grade)
        .order_by(PriceList.effective_from.desc(), PriceList.id.desc())
        .all()
    )
    results = []
    for e in entries:
        r = PriceListResponse.model_validate(e)
        r.crop_name = crop.name
        results.append(r)
    return results
