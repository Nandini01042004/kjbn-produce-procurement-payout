from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Crop
from app.schemas.crop import CropCreate, CropResponse
from app.domain.errors import EntityNotFoundError, DomainError

router = APIRouter(prefix="/crops", tags=["Crops"])


@router.get("", response_model=List[CropResponse])
def list_crops(db: Session = Depends(get_db)):
    """List all registered crops and their moisture thresholds and allowed grades."""
    return db.query(Crop).order_by(Crop.name.asc()).all()


@router.post("", response_model=CropResponse, status_code=status.HTTP_201_CREATED)
def create_crop(payload: CropCreate, db: Session = Depends(get_db)):
    """Register a new crop with allowed grades and moisture thresholds."""
    existing = db.query(Crop).filter(Crop.name.ilike(payload.name.strip())).first()
    if existing:
        raise DomainError(
            f"Crop '{payload.name}' already exists (ID #{existing.id}).",
            code="CROP_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT,
        )

    if payload.base_moisture_threshold > payload.max_moisture_accepted:
        raise DomainError(
            f"Base moisture threshold ({payload.base_moisture_threshold}%) cannot be greater "
            f"than max moisture accepted ({payload.max_moisture_accepted}%).",
            code="INVALID_MOISTURE_THRESHOLDS",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    crop = Crop(
        name=payload.name.strip(),
        allowed_grades=payload.allowed_grades,
        base_moisture_threshold=payload.base_moisture_threshold,
        max_moisture_accepted=payload.max_moisture_accepted,
    )
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop


@router.get("/{crop_id}", response_model=CropResponse)
def get_crop(crop_id: int, db: Session = Depends(get_db)):
    """Get crop details."""
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise EntityNotFoundError("Crop", crop_id)
    return crop
