"""Explicit OpenAI tool definitions and safe dispatch for business queries."""

import json
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.orm import Session

from app.services.business_queries import (
    get_product_details,
    query_campaigns,
    query_inventory,
    query_sales,
)

TOOL_DEFINITIONS = (
    {
        "type": "function",
        "name": "get_product_details",
        "description": "Get catalogue and margin details for one exact product SKU.",
        "parameters": {
            "type": "object",
            "properties": {"sku": {"type": "string", "description": "Exact product SKU."}},
            "required": ["sku"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "query_sales",
        "description": "Get aggregated sales, revenue, and gross profit by product.",
        "parameters": {
            "type": "object",
            "properties": {
                "sku": {"type": ["string", "null"], "description": "Optional exact product SKU."},
                "start_date": {"type": ["string", "null"], "description": "Optional inclusive ISO date, YYYY-MM-DD."},
                "end_date": {"type": ["string", "null"], "description": "Optional inclusive ISO date, YYYY-MM-DD."},
            },
            "required": ["sku", "start_date", "end_date"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "query_inventory",
        "description": "Get current inventory, available stock, and reorder status.",
        "parameters": {
            "type": "object",
            "properties": {
                "sku": {"type": ["string", "null"], "description": "Optional exact product SKU."}
            },
            "required": ["sku"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "query_campaigns",
        "description": "Get campaign performance and ROI.",
        "parameters": {
            "type": "object",
            "properties": {
                "sku": {"type": ["string", "null"], "description": "Optional exact product SKU."},
                "status": {"type": ["string", "null"], "description": "Optional campaign status."},
            },
            "required": ["sku", "status"],
            "additionalProperties": False,
        },
        "strict": True,
    },
)


class ToolDispatchError(ValueError):
    """A controlled error for an untrusted model tool call."""


class _ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class _ProductDetailsArguments(_ToolArguments):
    sku: str = Field(min_length=1)


class _SalesArguments(_ToolArguments):
    sku: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class _InventoryArguments(_ToolArguments):
    sku: str | None = None


class _CampaignArguments(_ToolArguments):
    sku: str | None = None
    status: str | None = None


def _parse_arguments(arguments: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as error:
            raise ToolDispatchError("Tool arguments must be valid JSON.") from error
    elif isinstance(arguments, dict):
        parsed = arguments
    else:
        raise ToolDispatchError("Tool arguments must be a JSON object.")

    if not isinstance(parsed, dict):
        raise ToolDispatchError("Tool arguments must be a JSON object.")
    return parsed


def _parse_iso_date(value: str | None, field_name: str) -> date | None:
    if value is None:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        raise ToolDispatchError(f"{field_name} must be an ISO date in YYYY-MM-DD format.")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ToolDispatchError(f"{field_name} must be an ISO date in YYYY-MM-DD format.") from error


def _validated_arguments(tool_name: str, arguments: str | dict[str, Any]) -> dict[str, Any]:
    parsed = _parse_arguments(arguments)
    try:
        if tool_name == "get_product_details":
            return _ProductDetailsArguments.model_validate(parsed).model_dump()
        if tool_name == "query_sales":
            values = _SalesArguments.model_validate(parsed).model_dump()
            start_date = _parse_iso_date(values["start_date"], "start_date")
            end_date = _parse_iso_date(values["end_date"], "end_date")
            if start_date is not None and end_date is not None and start_date > end_date:
                raise ToolDispatchError("start_date must not be after end_date.")
            return {
                "sku": values["sku"],
                "start_date": start_date,
                "end_date": end_date,
            }
        if tool_name == "query_inventory":
            return _InventoryArguments.model_validate(parsed).model_dump()
        if tool_name == "query_campaigns":
            return _CampaignArguments.model_validate(parsed).model_dump()
    except ValidationError as error:
        raise ToolDispatchError("Tool arguments do not match the required schema.") from error
    raise ToolDispatchError(f"Unsupported tool: {tool_name}.")


def validate_tool_arguments(
    tool_name: str, arguments: str | dict[str, Any]
) -> dict[str, Any]:
    """Validate a tool request and return stable JSON-compatible arguments."""
    return json_safe(_validated_arguments(tool_name, arguments))


def json_safe(value: Any) -> Any:
    """Convert deterministic business-query values to JSON-compatible primitives."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def dispatch_tool(
    session: Session, tool_name: str, arguments: str | dict[str, Any]
) -> dict[str, Any]:
    """Validate and execute one allowlisted business-query function."""
    validated = _validated_arguments(tool_name, arguments)

    data: object
    if tool_name == "get_product_details":
        data = get_product_details(session, validated["sku"])
    elif tool_name == "query_sales":
        data = query_sales(session, **validated)
    elif tool_name == "query_inventory":
        data = query_inventory(session, **validated)
    elif tool_name == "query_campaigns":
        data = query_campaigns(session, **validated)
    else:
        raise ToolDispatchError(f"Unsupported tool: {tool_name}.")

    return {
        "tool": tool_name,
        "arguments": json_safe(validated),
        "data": json_safe(data),
    }
