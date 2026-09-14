from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.db.seed import seed_demo_data
from app.services.llm_tools import (
    TOOL_DEFINITIONS,
    ToolDispatchError,
    dispatch_tool,
    json_safe,
)


def test_tool_definitions_expose_only_the_four_intended_tools() -> None:
    assert [tool["name"] for tool in TOOL_DEFINITIONS] == [
        "get_product_details",
        "query_sales",
        "query_inventory",
        "query_campaigns",
    ]
    assert all(tool["strict"] is True for tool in TOOL_DEFINITIONS)
    assert all(tool["parameters"]["additionalProperties"] is False for tool in TOOL_DEFINITIONS)
    assert TOOL_DEFINITIONS[1]["parameters"]["required"] == ["sku", "start_date", "end_date"]
    assert TOOL_DEFINITIONS[1]["parameters"]["properties"]["sku"]["type"] == ["string", "null"]


def test_dispatches_product_details_with_real_business_query(session: Session) -> None:
    seed_demo_data(session)

    result = dispatch_tool(session, "get_product_details", '{"sku":"FW-100"}')

    assert result["tool"] == "get_product_details"
    assert result["arguments"] == {"sku": "FW-100"}
    assert result["data"]["gross_margin"] == "23.49"


def test_dispatches_sales_with_date_conversion_and_filtering(session: Session) -> None:
    seed_demo_data(session)

    result = dispatch_tool(
        session,
        "query_sales",
        {"sku": "FW-100", "start_date": "2026-09-01", "end_date": "2026-09-30"},
    )

    assert result["arguments"] == {
        "sku": "FW-100",
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
    }
    assert result["data"] == [
        {
            "sku": "FW-100",
            "name": "Forest Builder Blocks",
            "units_sold": 90,
            "revenue": "3599.10",
            "gross_profit": "2114.10",
        }
    ]


def test_dispatches_inventory_and_campaigns_with_real_business_queries(session: Session) -> None:
    seed_demo_data(session)

    inventory = dispatch_tool(session, "query_inventory", {"sku": "FW-100"})
    campaigns = dispatch_tool(session, "query_campaigns", {"status": "active"})

    assert inventory["data"][0]["available_stock"] == 22
    assert {campaign["campaign"] for campaign in campaigns["data"]} == {
        "Peak Ambassador",
        "Turbo Video Launch",
    }


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        ("delete_everything", {}),
        ("query_inventory", "not json"),
        ("query_inventory", {"sku": "FW-100", "unexpected": "value"}),
        ("query_sales", {"start_date": "09/01/2026"}),
        ("query_sales", {"start_date": "20260901"}),
        ("query_sales", {"start_date": "2026-09-30", "end_date": "2026-09-01"}),
    ],
)
def test_dispatcher_rejects_unknown_or_invalid_calls(
    session: Session, tool_name: str, arguments: str | dict[str, str]
) -> None:
    with pytest.raises(ToolDispatchError):
        dispatch_tool(session, tool_name, arguments)


def test_json_safe_serializes_decimal_date_and_datetime() -> None:
    assert json_safe(
        {"money": Decimal("1.20"), "day": date(2026, 9, 7), "moment": datetime(2026, 9, 7, 9, 0)}
    ) == {
        "money": "1.20",
        "day": "2026-09-07",
        "moment": "2026-09-07T09:00:00",
    }
