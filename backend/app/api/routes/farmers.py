from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Farmer
from app.schemas.farmer import FarmerCreate, FarmerResponse
from app.schemas.payout import FarmerLedgerResponse
from app.domain.services import FarmerLedgerService
from app.domain.errors import EntityNotFoundError, DomainError

router = APIRouter(prefix="/farmers", tags=["Farmers"])


@router.get("", response_model=List[FarmerResponse])
def list_farmers(
    search: Optional[str] = Query(None, description="Search by name, phone, or village"),
    db: Session = Depends(get_db),
):
    """Retrieve list of farmers with current outstanding advances."""
    query = db.query(Farmer)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (Farmer.name.ilike(s)) | (Farmer.phone.ilike(s)) | (Farmer.village.ilike(s))
        )
    return query.order_by(Farmer.name.asc()).all()


@router.post("", response_model=FarmerResponse, status_code=status.HTTP_201_CREATED)
def create_farmer(payload: FarmerCreate, db: Session = Depends(get_db)):
    """Register a new farmer in the buying centre."""
    existing = db.query(Farmer).filter(Farmer.phone == payload.phone).first()
    if existing:
        raise DomainError(
            f"A farmer with phone number '{payload.phone}' already exists (#{existing.id}: {existing.name}).",
            code="PHONE_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT,
        )

    farmer = Farmer(
        name=payload.name.strip(),
        phone=payload.phone.strip(),
        village=payload.village.strip(),
        bank_reference=payload.bank_reference.strip(),
        outstanding_advance=payload.outstanding_advance or 0,
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer


@router.get("/{farmer_id}", response_model=FarmerResponse)
def get_farmer(farmer_id: int, db: Session = Depends(get_db)):
    """Get single farmer details."""
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise EntityNotFoundError("Farmer", farmer_id)
    return farmer


@router.get("/{farmer_id}/ledger", response_model=FarmerLedgerResponse)
def get_farmer_ledger(farmer_id: int, db: Session = Depends(get_db)):
    """Retrieve comprehensive financial ledger for a farmer (deliveries, advances, payouts, balance)."""
    return FarmerLedgerService.get_ledger(db, farmer_id)
