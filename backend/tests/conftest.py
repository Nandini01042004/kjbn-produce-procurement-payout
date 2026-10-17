import os
import sys
from decimal import Decimal
from datetime import date, datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base
from app.models import Farmer, Crop, PriceList, Delivery, Advance, Payout
from app.clock import set_global_clock

UTC = timezone.utc
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Provides a fresh in-memory SQLite database session for each test."""
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    set_global_clock(datetime(2026, 10, 17, 12, 0, 0, tzinfo=UTC))
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        set_global_clock(None)


@pytest.fixture
def sample_crop(db_session):
    crop = Crop(
        name="Maize",
        allowed_grades=["A", "B", "C"],
        base_moisture_threshold=Decimal("14.00"),
        max_moisture_accepted=Decimal("20.00"),
    )
    db_session.add(crop)
    db_session.commit()
    db_session.refresh(crop)
    return crop


@pytest.fixture
def sample_prices(db_session, sample_crop):
    p1 = PriceList(
        crop_id=sample_crop.id,
        grade="A",
        price_per_kg=Decimal("22.00"),
        effective_from=date(2026, 9, 1),
    )
    p2 = PriceList(
        crop_id=sample_crop.id,
        grade="A",
        price_per_kg=Decimal("24.50"),
        effective_from=date(2026, 10, 1),
    )
    p3 = PriceList(
        crop_id=sample_crop.id,
        grade="B",
        price_per_kg=Decimal("20.00"),
        effective_from=date(2026, 9, 1),
    )
    db_session.add_all([p1, p2, p3])
    db_session.commit()
    return [p1, p2, p3]


@pytest.fixture
def sample_farmer(db_session):
    farmer = Farmer(
        name="Ramesh Patel",
        phone="9876543210",
        village="Hunsur",
        bank_reference="SBIN0001234-9871029384",
        outstanding_advance=Decimal("5000.00"),
    )
    db_session.add(farmer)
    db_session.commit()
    db_session.refresh(farmer)
    return farmer
