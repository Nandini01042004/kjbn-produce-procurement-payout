from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.clock import get_current_time, format_ist
from seed import seed_database

router = APIRouter(tags=["Health & Admin"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint providing system status, database connectivity, and current clocks."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    now_utc = get_current_time()
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "KJBN Produce Procurement & Payout Engine",
        "version": "1.0.0",
        "database": db_status,
        "clock": {
            "utc": now_utc.isoformat(),
            "ist": format_ist(now_utc),
        },
    }


@router.post("/admin/reset-seed")
def reset_seed():
    """Reviewer aid: Reset database to initial seed data state."""
    seed_database()
    return {"status": "ok", "message": "Database successfully reset and seeded with initial data."}
