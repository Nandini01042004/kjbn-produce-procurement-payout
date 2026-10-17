from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Delivery, Farmer, Crop
from app.schemas.delivery import (
    DeliveryPreviewRequest,
    DeliveryPreviewResponse,
    DeliveryCreate,
    DeliveryResponse,
)
from app.domain.services import DeliveryService
from app.domain.errors import EntityNotFoundError

router = APIRouter(prefix="/deliveries", tags=["Deliveries"])


@router.post("/preview", response_model=DeliveryPreviewResponse)
def preview_delivery(payload: DeliveryPreviewRequest, db: Session = Depends(get_db)):
    """
    Live delivery preview calculation before saving.
    Evaluates applicable effective price, computes moisture penalty, net kg, and amount.
    """
    return DeliveryService.preview(db, payload)


@router.post("", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
def create_delivery(payload: DeliveryCreate, db: Session = Depends(get_db)):
    """
    Record a new produce delivery with frozen breakdown (gross kg, deduction %, deduction kg, net kg, applied price, amount).
    Supports credit/debit note corrections by referencing original delivery.
    """
    delivery = DeliveryService.create(db, payload)
    resp = DeliveryResponse.model_validate(delivery)
    resp.farmer_name = delivery.farmer.name if delivery.farmer else None
    resp.crop_name = delivery.crop.name if delivery.crop else None
    return resp


@router.get("", response_model=List[DeliveryResponse])
def list_deliveries(
    farmer_id: Optional[int] = Query(None, description="Filter by farmer ID"),
    crop_id: Optional[int] = Query(None, description="Filter by crop ID"),
    payout_id: Optional[int] = Query(None, description="Filter by payout ID"),
    unassigned_only: bool = Query(False, description="Filter for deliveries not yet in any payout"),
    db: Session = Depends(get_db),
):
    """List deliveries with comprehensive breakdown and filtering."""
    query = db.query(Delivery).join(Farmer).join(Crop)
    if farmer_id:
        query = query.filter(Delivery.farmer_id == farmer_id)
    if crop_id:
        query = query.filter(Delivery.crop_id == crop_id)
    if payout_id:
        query = query.filter(Delivery.payout_id == payout_id)
    if unassigned_only:
        query = query.filter(Delivery.payout_id == None)

    deliveries = query.order_by(Delivery.delivered_on.desc(), Delivery.id.desc()).all()
    results = []
    for d in deliveries:
        r = DeliveryResponse.model_validate(d)
        r.farmer_name = d.farmer.name if d.farmer else None
        r.crop_name = d.crop.name if d.crop else None
        results.append(r)
    return results


@router.get("/{delivery_id}", response_model=DeliveryResponse)
def get_delivery(delivery_id: int, db: Session = Depends(get_db)):
    """Get single delivery with complete breakdown."""
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise EntityNotFoundError("Delivery", delivery_id)

    resp = DeliveryResponse.model_validate(delivery)
    resp.farmer_name = delivery.farmer.name if delivery.farmer else None
    resp.crop_name = delivery.crop.name if delivery.crop else None
    return resp
