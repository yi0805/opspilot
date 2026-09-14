"""Focused, deterministic queries over OpsPilot business data."""

from datetime import date
from decimal import Decimal
from typing import TypedDict

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models import Campaign, Inventory, Product, Sale


class SalesSummary(TypedDict):
    sku: str
    name: str
    units_sold: int
    revenue: Decimal
    gross_profit: Decimal


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def get_product_details(session: Session, sku: str) -> dict[str, object] | None:
    """Return product details for an exact SKU, or ``None`` when it is unknown."""
    product = session.scalar(select(Product).where(Product.sku == sku))
    if product is None:
        return None

    gross_margin = product.unit_price - product.unit_cost
    return {
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "unit_price": product.unit_price,
        "unit_cost": product.unit_cost,
        "gross_margin": _money(gross_margin),
        "gross_margin_percent": (gross_margin / product.unit_price * Decimal("100")).quantize(
            Decimal("0.01")
        ),
        "reorder_point": product.reorder_point,
        "active": product.active,
    }


def query_sales(
    session: Session,
    *,
    sku: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, object]]:
    """Aggregate units, revenue, and gross profit by product."""
    statement: Select[tuple[Sale]] = select(Sale).options(joinedload(Sale.product))
    if sku is not None:
        statement = statement.join(Sale.product).where(Product.sku == sku)
    if start_date is not None:
        statement = statement.where(Sale.sale_date >= start_date)
    if end_date is not None:
        statement = statement.where(Sale.sale_date <= end_date)

    summaries: dict[str, SalesSummary] = {}
    for sale in session.scalars(statement.order_by(Sale.sale_date)).unique():
        summary = summaries.setdefault(
            sale.product.sku,
            {
                "sku": sale.product.sku,
                "name": sale.product.name,
                "units_sold": 0,
                "revenue": Decimal("0.00"),
                "gross_profit": Decimal("0.00"),
            },
        )
        summary["units_sold"] = int(summary["units_sold"]) + sale.units_sold
        summary["revenue"] = summary["revenue"] + sale.units_sold * sale.unit_price
        summary["gross_profit"] = summary["gross_profit"] + sale.units_sold * (
            sale.unit_price - sale.product.unit_cost
        )

    return [
        {
            **summary,
            "revenue": _money(summary["revenue"]),
            "gross_profit": _money(summary["gross_profit"]),
        }
        for summary in summaries.values()
    ]


def query_inventory(session: Session, *, sku: str | None = None) -> list[dict[str, object]]:
    """Return current product inventory and its deterministic reorder status."""
    statement = select(Inventory).join(Inventory.product).options(joinedload(Inventory.product))
    if sku is not None:
        statement = statement.join(Inventory.product).where(Product.sku == sku)

    inventory_rows = session.scalars(statement.order_by(Product.sku)).unique()
    results: list[dict[str, object]] = []
    for inventory in inventory_rows:
        available_stock = inventory.on_hand - inventory.reserved
        results.append(
            {
                "sku": inventory.product.sku,
                "name": inventory.product.name,
                "on_hand": inventory.on_hand,
                "reserved": inventory.reserved,
                "available_stock": available_stock,
                "incoming": inventory.incoming,
                "reorder_point": inventory.product.reorder_point,
                "at_or_below_reorder_point": available_stock <= inventory.product.reorder_point,
            }
        )
    return results


def query_campaigns(
    session: Session,
    *,
    sku: str | None = None,
    status: str | None = None,
) -> list[dict[str, object]]:
    """Return campaign performance with safe ROI calculations."""
    statement = select(Campaign).options(joinedload(Campaign.product))
    if sku is not None:
        statement = statement.join(Campaign.product).where(Product.sku == sku)
    if status is not None:
        statement = statement.where(Campaign.status == status)

    results: list[dict[str, object]] = []
    for campaign in session.scalars(statement.order_by(Campaign.name)).unique():
        roi = None
        if campaign.spend != Decimal("0.00"):
            roi = ((campaign.attributed_revenue - campaign.spend) / campaign.spend).quantize(
                Decimal("0.0001")
            )
        results.append(
            {
                "campaign": campaign.name,
                "channel": campaign.channel,
                "sku": campaign.product.sku,
                "product": campaign.product.name,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "spend": campaign.spend,
                "attributed_revenue": campaign.attributed_revenue,
                "roi": roi,
                "status": campaign.status,
            }
        )
    return results
