"""
Seed Script for Farm Produce Buying Centre
Seeds realistic Indian agricultural data (Maize, Turmeric, Groundnut),
multiple price-list tiers over time, farmers, advances, deliveries, and past payouts.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from app.database import engine, SessionLocal, Base
from app.models import Farmer, Crop, PriceList, Delivery, Advance, Payout
from app.clock import set_global_clock

UTC = timezone.utc


def seed_database():
    print("[SEED] Resetting database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("[SEED] Creating Crops...")
        maize = Crop(
            name="Maize",
            allowed_grades=["A", "B", "C"],
            base_moisture_threshold=Decimal("14.00"),
            max_moisture_accepted=Decimal("20.00"),
        )
        turmeric = Crop(
            name="Turmeric",
            allowed_grades=["A", "B"],
            base_moisture_threshold=Decimal("12.00"),
            max_moisture_accepted=Decimal("18.00"),
        )
        groundnut = Crop(
            name="Groundnut",
            allowed_grades=["A", "B"],
            base_moisture_threshold=Decimal("9.00"),
            max_moisture_accepted=Decimal("15.00"),
        )
        db.add_all([maize, turmeric, groundnut])
        db.commit()

        print("[SEED] Creating Effective-Dated Price Lists...")
        # Historic price entries (September 2026)
        prices = [
            # Maize - Sept 1, 2026
            PriceList(crop_id=maize.id, grade="A", price_per_kg=Decimal("22.00"), effective_from=date(2026, 9, 1)),
            PriceList(crop_id=maize.id, grade="B", price_per_kg=Decimal("20.00"), effective_from=date(2026, 9, 1)),
            PriceList(crop_id=maize.id, grade="C", price_per_kg=Decimal("18.00"), effective_from=date(2026, 9, 1)),
            # Maize - Oct 1, 2026 (Revised rates)
            PriceList(crop_id=maize.id, grade="A", price_per_kg=Decimal("24.50"), effective_from=date(2026, 10, 1)),
            PriceList(crop_id=maize.id, grade="B", price_per_kg=Decimal("22.00"), effective_from=date(2026, 10, 1)),
            PriceList(crop_id=maize.id, grade="C", price_per_kg=Decimal("19.50"), effective_from=date(2026, 10, 1)),
            # Turmeric - Sept 1, 2026
            PriceList(crop_id=turmeric.id, grade="A", price_per_kg=Decimal("72.00"), effective_from=date(2026, 9, 1)),
            PriceList(crop_id=turmeric.id, grade="B", price_per_kg=Decimal("65.00"), effective_from=date(2026, 9, 1)),
            # Turmeric - Oct 1, 2026
            PriceList(crop_id=turmeric.id, grade="A", price_per_kg=Decimal("78.00"), effective_from=date(2026, 10, 1)),
            PriceList(crop_id=turmeric.id, grade="B", price_per_kg=Decimal("70.00"), effective_from=date(2026, 10, 1)),
            # Groundnut - Sept 15, 2026
            PriceList(crop_id=groundnut.id, grade="A", price_per_kg=Decimal("58.00"), effective_from=date(2026, 9, 15)),
            PriceList(crop_id=groundnut.id, grade="B", price_per_kg=Decimal("52.00"), effective_from=date(2026, 9, 15)),
            # Groundnut - Oct 10, 2026
            PriceList(crop_id=groundnut.id, grade="A", price_per_kg=Decimal("62.50"), effective_from=date(2026, 10, 10)),
            PriceList(crop_id=groundnut.id, grade="B", price_per_kg=Decimal("56.00"), effective_from=date(2026, 10, 10)),
        ]
        db.add_all(prices)
        db.commit()

        print("[SEED] Creating Farmers...")
        f1 = Farmer(
            name="Ramesh Patel",
            phone="9876543210",
            village="Hunsur",
            bank_reference="SBIN0001234-9871029384",
            outstanding_advance=Decimal("5000.00"),
        )
        f2 = Farmer(
            name="Suresh Gowda",
            phone="9876543211",
            village="Mandya",
            bank_reference="KARB0000456-1123581321",
            outstanding_advance=Decimal("15000.00"),
        )
        f3 = Farmer(
            name="Lakshmi Devi",
            phone="9876543212",
            village="Maddur",
            bank_reference="CNRB0002345-5544332211",
            outstanding_advance=Decimal("0.00"),
        )
        f4 = Farmer(
            name="Anjanappa M",
            phone="9876543213",
            village="Ramanagara",
            bank_reference="BARB0KOLKAT-8899001122",
            outstanding_advance=Decimal("25000.00"),
        )
        db.add_all([f1, f2, f3, f4])
        db.commit()

        print("[SEED] Creating Advances...")
        # Advances for farmers
        adv1 = Advance(
            farmer_id=f1.id,
            amount=Decimal("5000.00"),
            given_on=datetime(2026, 10, 5, 10, 0, tzinfo=UTC),
            notes="Pre-harvest fertilizer support",
        )
        adv2 = Advance(
            farmer_id=f2.id,
            amount=Decimal("15000.00"),
            given_on=datetime(2026, 10, 2, 11, 30, tzinfo=UTC),
            notes="Equipment diesel advance",
        )
        adv4 = Advance(
            farmer_id=f4.id,
            amount=Decimal("25000.00"),
            given_on=datetime(2026, 9, 28, 9, 15, tzinfo=UTC),
            notes="Irrigation pump maintenance advance",
        )
        db.add_all([adv1, adv2, adv4])
        db.commit()

        print("[SEED] Creating Past Finalised Payout and Historical Delivery...")
        # Week of Sept 21-27, 2026
        # P1 for Ramesh Patel: delivered maize
        # Maize A on 2026-09-22: applied price 22.00
        p_price_m1 = next(p for p in prices if p.crop_id == maize.id and p.grade == "A" and p.effective_from == date(2026, 9, 1))
        # 1000 kg, 15.0% moisture (14% threshold -> 1% deduction)
        # deduction_kg = 10.00, net_kg = 990.00, amount = 990 * 22 = 21780.00
        deliv_hist = Delivery(
            farmer_id=f1.id,
            crop_id=maize.id,
            grade="A",
            gross_weight_kg=Decimal("1000.00"),
            moisture=Decimal("15.00"),
            delivered_on=datetime(2026, 9, 22, 11, 0, tzinfo=UTC),
            gross_kg=Decimal("1000.00"),
            deduction_pct=Decimal("1.00"),
            deduction_kg=Decimal("10.00"),
            net_kg=Decimal("990.00"),
            applied_price=Decimal("22.00"),
            applied_price_list_id=p_price_m1.id,
            amount=Decimal("21780.00"),
        )
        db.add(deliv_hist)
        db.commit()

        past_payout = Payout(
            farmer_id=f1.id,
            week_start=date(2026, 9, 21),
            week_end=date(2026, 9, 27),
            gross_amount=Decimal("21780.00"),
            advance_deduction=Decimal("0.00"),
            net_amount=Decimal("21780.00"),
            status="Finalised",
            finalised_at=datetime(2026, 9, 28, 14, 0, tzinfo=UTC),
        )
        db.add(past_payout)
        db.commit()

        deliv_hist.payout_id = past_payout.id
        db.commit()

        print("[SEED] Creating Active Unpaid Deliveries for Week of Oct 12-18, 2026...")
        # Active price list entries for October
        p_oct_maize_a = next(p for p in prices if p.crop_id == maize.id and p.grade == "A" and p.effective_from == date(2026, 10, 1))
        p_oct_turmeric_a = next(p for p in prices if p.crop_id == turmeric.id and p.grade == "A" and p.effective_from == date(2026, 10, 1))
        p_oct_groundnut_a = next(p for p in prices if p.crop_id == groundnut.id and p.grade == "A" and p.effective_from == date(2026, 10, 10))

        # Delivery 1: Ramesh Patel - Maize Grade A, 1200 kg, 17.6% moisture (14% threshold -> 3% deduction)
        # gross = 1200.00, deduction_pct = 3.00, deduction_kg = 36.00, net_kg = 1164.00, price = 24.50, amount = 28518.00
        d1 = Delivery(
            farmer_id=f1.id,
            crop_id=maize.id,
            grade="A",
            gross_weight_kg=Decimal("1200.00"),
            moisture=Decimal("17.60"),
            delivered_on=datetime(2026, 10, 13, 10, 30, tzinfo=UTC),
            gross_kg=Decimal("1200.00"),
            deduction_pct=Decimal("3.00"),
            deduction_kg=Decimal("36.00"),
            net_kg=Decimal("1164.00"),
            applied_price=Decimal("24.50"),
            applied_price_list_id=p_oct_maize_a.id,
            amount=Decimal("28518.00"),
        )

        # Delivery 2: Ramesh Patel - Turmeric Grade A, 400 kg, 12.0% moisture (12% threshold -> 0% deduction)
        # gross = 400.00, deduction_pct = 0.00, deduction_kg = 0.00, net_kg = 400.00, price = 78.00, amount = 31200.00
        d2 = Delivery(
            farmer_id=f1.id,
            crop_id=turmeric.id,
            grade="A",
            gross_weight_kg=Decimal("400.00"),
            moisture=Decimal("12.00"),
            delivered_on=datetime(2026, 10, 14, 15, 0, tzinfo=UTC),
            gross_kg=Decimal("400.00"),
            deduction_pct=Decimal("0.00"),
            deduction_kg=Decimal("0.00"),
            net_kg=Decimal("400.00"),
            applied_price=Decimal("78.00"),
            applied_price_list_id=p_oct_turmeric_a.id,
            amount=Decimal("31200.00"),
        )

        # Delivery 3: Suresh Gowda - Groundnut Grade A, 850 kg, 11.2% moisture (9% threshold -> 2% deduction)
        # gross = 850.00, deduction_pct = 2.00, deduction_kg = 17.00, net_kg = 833.00, price = 62.50, amount = 52062.50
        d3 = Delivery(
            farmer_id=f2.id,
            crop_id=groundnut.id,
            grade="A",
            gross_weight_kg=Decimal("850.00"),
            moisture=Decimal("11.20"),
            delivered_on=datetime(2026, 10, 14, 11, 45, tzinfo=UTC),
            gross_kg=Decimal("850.00"),
            deduction_pct=Decimal("2.00"),
            deduction_kg=Decimal("17.00"),
            net_kg=Decimal("833.00"),
            applied_price=Decimal("62.50"),
            applied_price_list_id=p_oct_groundnut_a.id,
            amount=Decimal("52062.50"),
        )

        # Delivery 4: Lakshmi Devi - Maize Grade A, 1500 kg, 14.99% moisture (14% threshold -> 0% deduction!)
        # gross = 1500.00, deduction_pct = 0.00, deduction_kg = 0.00, net_kg = 1500.00, price = 24.50, amount = 36750.00
        d4 = Delivery(
            farmer_id=f3.id,
            crop_id=maize.id,
            grade="A",
            gross_weight_kg=Decimal("1500.00"),
            moisture=Decimal("14.99"),
            delivered_on=datetime(2026, 10, 15, 9, 30, tzinfo=UTC),
            gross_kg=Decimal("1500.00"),
            deduction_pct=Decimal("0.00"),
            deduction_kg=Decimal("0.00"),
            net_kg=Decimal("1500.00"),
            applied_price=Decimal("24.50"),
            applied_price_list_id=p_oct_maize_a.id,
            amount=Decimal("36750.00"),
        )

        db.add_all([d1, d2, d3, d4])
        db.commit()

        print("[SEED] Successfully seeded database with realistic sample data!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
