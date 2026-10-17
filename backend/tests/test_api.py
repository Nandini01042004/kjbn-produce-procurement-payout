"""
API Integration Tests for KJBN Produce Procurement & Payout
Tests full HTTP request/response lifecycles, error envelopes, and clock overrides.
"""

from decimal import Decimal
from datetime import date, datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db

UTC = timezone.utc


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_api_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "clock" in data
    assert "database" in data


def test_api_reviewer_clock_override(client):
    # Pass X-Test-Clock header
    test_clock = "2026-10-15T09:00:00Z"
    response = client.get("/api/health", headers={"X-Test-Clock": test_clock})
    assert response.status_code == 200
    data = response.json()
    assert "2026-10-15" in data["clock"]["utc"]


def test_api_create_farmer_and_list(client):
    payload = {
        "name": "Naveen Kumar",
        "phone": "9988776655",
        "village": "Periyapatna",
        "bank_reference": "SBIN0009999-123456",
        "outstanding_advance": "3000.00",
    }
    create_res = client.post("/api/farmers", json=payload)
    assert create_res.status_code == 201
    farmer_data = create_res.json()
    assert farmer_data["name"] == "Naveen Kumar"
    assert Decimal(str(farmer_data["outstanding_advance"])) == Decimal("3000.00")

    # List farmers
    list_res = client.get("/api/farmers")
    assert list_res.status_code == 200
    assert any(f["phone"] == "9988776655" for f in list_res.json())


def test_api_delivery_preview(client, sample_crop, sample_prices):
    preview_req = {
        "crop_id": sample_crop.id,
        "grade": "A",
        "gross_weight_kg": "1000.00",
        "moisture": "17.60",
        "delivered_on": "2026-10-15T10:00:00Z",
    }
    res = client.post("/api/deliveries/preview", json=preview_req)
    assert res.status_code == 200
    data = res.json()
    breakdown = data["breakdown"]
    assert Decimal(str(breakdown["deduction_pct"])) == Decimal("3.00")
    assert Decimal(str(breakdown["net_kg"])) == Decimal("970.00")
    assert Decimal(str(breakdown["applied_price"])) == Decimal("24.50")
    assert Decimal(str(breakdown["amount"])) == Decimal("23765.00")


def test_api_delivery_create_and_ledger(client, sample_farmer, sample_crop, sample_prices):
    delivery_req = {
        "farmer_id": sample_farmer.id,
        "crop_id": sample_crop.id,
        "grade": "A",
        "gross_weight_kg": "1000.00",
        "moisture": "14.00",
        "delivered_on": "2026-10-14T10:00:00Z",
    }
    create_res = client.post("/api/deliveries", json=delivery_req)
    assert create_res.status_code == 201
    deliv_data = create_res.json()
    assert deliv_data["applied_price_list_id"] is not None
    assert Decimal(str(deliv_data["amount"])) == Decimal("24500.00")

    # Check farmer ledger
    ledger_res = client.get(f"/api/farmers/{sample_farmer.id}/ledger")
    assert ledger_res.status_code == 200
    ledger_data = ledger_res.json()
    assert ledger_data["total_deliveries_count"] == 1
    assert Decimal(str(ledger_data["total_gross_earnings"])) == Decimal("24500.00")


def test_api_payout_lifecycle(client, sample_farmer, sample_crop, sample_prices):
    # 1. Create a delivery on Wednesday Oct 14, 2026
    delivery_req = {
        "farmer_id": sample_farmer.id,
        "crop_id": sample_crop.id,
        "grade": "A",
        "gross_weight_kg": "1000.00",
        "moisture": "14.00",
        "delivered_on": "2026-10-14T10:00:00Z",
    }
    client.post("/api/deliveries", json=delivery_req)

    # 2. Generate Draft payout for the week of Oct 14
    gen_res = client.post(
        "/api/payouts/generate",
        json={"farmer_id": sample_farmer.id, "for_date": "2026-10-14"},
    )
    assert gen_res.status_code == 200
    payout_data = gen_res.json()
    assert payout_data["status"] == "Draft"
    assert Decimal(str(payout_data["gross_amount"])) == Decimal("24500.00")
    # Outstanding advance was 5000. 30% of 24500 is 7350. So 5000 is deducted.
    assert Decimal(str(payout_data["advance_deduction"])) == Decimal("5000.00")
    assert Decimal(str(payout_data["net_amount"])) == Decimal("19500.00")

    payout_id = payout_data["id"]

    # 3. Finalise Payout
    fin_res = client.post(f"/api/payouts/{payout_id}/finalise")
    assert fin_res.status_code == 200
    fin_data = fin_res.json()
    assert fin_data["status"] == "Finalised"

    # Verify farmer outstanding advance is now zero
    farmer_res = client.get(f"/api/farmers/{sample_farmer.id}")
    assert Decimal(str(farmer_res.json()["outstanding_advance"])) == Decimal("0.00")

    # 4. Mark Paid
    paid_res = client.post(f"/api/payouts/{payout_id}/mark-paid")
    assert paid_res.status_code == 200
    assert paid_res.json()["status"] == "Paid"


def test_api_error_response_shape_on_domain_violation(client, sample_crop):
    # Moisture exceeded should return 422 with standardized JSON envelope
    preview_req = {
        "crop_id": sample_crop.id,
        "grade": "A",
        "gross_weight_kg": "1000.00",
        "moisture": "25.00",  # Max is 20%
        "delivered_on": "2026-10-15T10:00:00Z",
    }
    res = client.post("/api/deliveries/preview", json=preview_req)
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "MAX_MOISTURE_EXCEEDED"
    assert "request_id" in data["error"]
    assert "exceeds maximum accepted moisture" in data["error"]["message"]


def test_api_error_response_shape_on_missing_entity(client):
    res = client.get("/api/farmers/999999")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "ENTITY_NOT_FOUND"


def test_api_bad_request_validation_handling(client):
    # Malformed payload (missing fields, wrong types)
    res = client.post("/api/farmers", json={"invalid": "payload"})
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0
