"""Deterministic synthetic data for local OpsPilot demonstrations."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.models  # Ensure all model metadata is registered before create_all().
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Campaign, Inventory, Product, Sale


PRODUCTS = (
    ("FW-100", "Forest Builder Blocks", "Toys", "39.99", "16.50", 30),
    ("TB-200", "Turbo Track Set", "Toys", "59.99", "28.00", 20),
    ("AR-300", "Artist Studio Kit", "Creative", "24.99", "9.50", 25),
    ("DK-400", "Discovery Lab Kit", "Educational", "44.99", "21.00", 15),
    ("HB-500", "Home Base Organizer", "Home", "34.99", "13.00", 40),
    ("PT-600", "Peak Performance Bottle", "Lifestyle", "19.99", "5.75", 35),
    ("GL-700", "Garden Glow Lights", "Home", "29.99", "11.00", 20),
    ("MS-800", "Mini Maker Robot", "Educational", "79.99", "39.00", 10),
    ("CT-900", "City Transit Puzzle", "Creative", "18.99", "7.00", 30),
)

SALES = (
    ("FW-100", date(2026, 8, 16), 120), ("FW-100", date(2026, 8, 30), 100), ("FW-100", date(2026, 9, 6), 90),
    ("TB-200", date(2026, 8, 16), 55), ("TB-200", date(2026, 8, 30), 48), ("TB-200", date(2026, 9, 6), 42),
    ("AR-300", date(2026, 8, 16), 70), ("AR-300", date(2026, 8, 30), 66), ("AR-300", date(2026, 9, 6), 72),
    ("DK-400", date(2026, 8, 16), 32), ("DK-400", date(2026, 8, 30), 36), ("DK-400", date(2026, 9, 6), 40),
    ("HB-500", date(2026, 8, 16), 5), ("HB-500", date(2026, 8, 30), 4), ("HB-500", date(2026, 9, 6), 3),
    ("PT-600", date(2026, 8, 16), 60), ("PT-600", date(2026, 8, 30), 64), ("PT-600", date(2026, 9, 6), 68),
    ("GL-700", date(2026, 8, 16), 18), ("GL-700", date(2026, 8, 30), 22), ("GL-700", date(2026, 9, 6), 20),
    ("MS-800", date(2026, 8, 16), 24), ("MS-800", date(2026, 8, 30), 20), ("MS-800", date(2026, 9, 6), 28),
    ("CT-900", date(2026, 8, 16), 26), ("CT-900", date(2026, 8, 30), 24), ("CT-900", date(2026, 9, 6), 22),
)

INVENTORY = (
    ("FW-100", 28, 6, 120), ("TB-200", 54, 8, 60), ("AR-300", 82, 10, 0),
    ("DK-400", 30, 4, 36), ("HB-500", 200, 15, 0), ("PT-600", 48, 7, 96),
    ("GL-700", 70, 5, 40), ("MS-800", 18, 3, 24), ("CT-900", 65, 8, 0),
)

CAMPAIGNS = (
    ("Creator Spotlight", "Influencer", "AR-300", date(2026, 8, 1), date(2026, 8, 31), "400.00", "1800.00", "completed"),
    ("Search Conversion", "Search", "DK-400", date(2026, 8, 10), date(2026, 9, 10), "650.00", "1400.00", "completed"),
    ("Turbo Video Launch", "Video", "TB-200", date(2026, 8, 15), date(2026, 9, 15), "900.00", "600.00", "active"),
    ("Home Re-engagement", "Email", "HB-500", date(2026, 8, 20), date(2026, 9, 10), "250.00", "180.00", "completed"),
    ("Peak Ambassador", "Influencer", "PT-600", date(2026, 9, 1), date(2026, 9, 30), "0.00", "300.00", "active"),
    ("City Puzzle Social", "Social", "CT-900", date(2026, 8, 5), date(2026, 8, 25), "350.00", "500.00", "completed"),
)


def seed_demo_data(session: Session) -> bool:
    """Insert the complete synthetic data set once; return whether rows were created."""
    if session.scalar(select(Product.id).limit(1)) is not None:
        return False

    products = {
        sku: Product(
            sku=sku,
            name=name,
            category=category,
            unit_price=Decimal(unit_price),
            unit_cost=Decimal(unit_cost),
            reorder_point=reorder_point,
            active=True,
        )
        for sku, name, category, unit_price, unit_cost, reorder_point in PRODUCTS
    }
    session.add_all(products.values())
    session.flush()

    session.add_all(
        Sale(product=products[sku], sale_date=sale_date, units_sold=units, unit_price=products[sku].unit_price)
        for sku, sale_date, units in SALES
    )
    session.add_all(
        Inventory(
            product=products[sku],
            on_hand=on_hand,
            reserved=reserved,
            incoming=incoming,
            updated_at=datetime(2026, 9, 7, 9, 0, 0),
        )
        for sku, on_hand, reserved, incoming in INVENTORY
    )
    session.add_all(
        Campaign(
            name=name,
            channel=channel,
            product=products[sku],
            start_date=start_date,
            end_date=end_date,
            spend=Decimal(spend),
            attributed_revenue=Decimal(attributed_revenue),
            status=status,
        )
        for name, channel, sku, start_date, end_date, spend, attributed_revenue, status in CAMPAIGNS
    )
    session.commit()
    return True


def main() -> None:
    """Create business tables and seed configured database for local demo use."""
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        created = seed_demo_data(session)
    print("Seeded synthetic OpsPilot business data." if created else "Synthetic data already exists; no changes made.")


if __name__ == "__main__":
    main()
