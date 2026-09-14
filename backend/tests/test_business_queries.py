from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.seed import seed_demo_data
from app.models import Campaign, Inventory, Product, Sale
from app.services.business_queries import (
    get_product_details,
    query_campaigns,
    query_inventory,
    query_sales,
)


def test_seed_creates_deterministic_dataset_once(session: Session) -> None:
    assert seed_demo_data(session) is True
    assert seed_demo_data(session) is False

    assert session.scalar(select(func.count()).select_from(Product)) == 9
    assert session.scalar(select(func.count()).select_from(Sale)) == 27
    assert session.scalar(select(func.count()).select_from(Inventory)) == 9
    assert session.scalar(select(func.count()).select_from(Campaign)) == 6


def test_product_lookup_returns_margin_details(session: Session) -> None:
    seed_demo_data(session)

    product = get_product_details(session, "FW-100")

    assert product == {
        "sku": "FW-100",
        "name": "Forest Builder Blocks",
        "category": "Toys",
        "unit_price": Decimal("39.99"),
        "unit_cost": Decimal("16.50"),
        "gross_margin": Decimal("23.49"),
        "gross_margin_percent": Decimal("58.74"),
        "reorder_point": 30,
        "active": True,
    }
    assert get_product_details(session, "UNKNOWN") is None


def test_sales_aggregation_and_date_filter_are_correct(session: Session) -> None:
    seed_demo_data(session)

    sales = query_sales(session, sku="FW-100")

    assert sales == [
        {
            "sku": "FW-100",
            "name": "Forest Builder Blocks",
            "units_sold": 310,
            "revenue": Decimal("12396.90"),
            "gross_profit": Decimal("7281.90"),
        }
    ]
    assert query_sales(session, sku="FW-100", start_date=date(2026, 9, 1)) == [
        {
            "sku": "FW-100",
            "name": "Forest Builder Blocks",
            "units_sold": 90,
            "revenue": Decimal("3599.10"),
            "gross_profit": Decimal("2114.10"),
        }
    ]


def test_inventory_calculates_available_stock_and_reorder_status(session: Session) -> None:
    seed_demo_data(session)

    forest_blocks = query_inventory(session, sku="FW-100")

    assert forest_blocks == [
        {
            "sku": "FW-100",
            "name": "Forest Builder Blocks",
            "on_hand": 28,
            "reserved": 6,
            "available_stock": 22,
            "incoming": 120,
            "reorder_point": 30,
            "at_or_below_reorder_point": True,
        }
    ]


def test_campaign_roi_handles_positive_negative_and_zero_spend(session: Session) -> None:
    seed_demo_data(session)

    campaigns = {campaign["campaign"]: campaign for campaign in query_campaigns(session)}

    assert campaigns["Creator Spotlight"]["roi"] == Decimal("3.5000")
    assert campaigns["Home Re-engagement"]["roi"] == Decimal("-0.2800")
    assert campaigns["Peak Ambassador"]["roi"] is None
    assert query_campaigns(session, status="active")


def test_demo_scenarios_include_sales_stock_and_campaign_variation(session: Session) -> None:
    seed_demo_data(session)

    sales = {row["sku"]: row for row in query_sales(session)}
    inventory = {row["sku"]: row for row in query_inventory(session)}
    campaigns = query_campaigns(session)

    assert sales["FW-100"]["units_sold"] > sales["HB-500"]["units_sold"]
    assert inventory["FW-100"]["at_or_below_reorder_point"] is True
    assert inventory["HB-500"]["available_stock"] > inventory["HB-500"]["reorder_point"]
    assert any(campaign["roi"] is not None and campaign["roi"] < 0 for campaign in campaigns)
