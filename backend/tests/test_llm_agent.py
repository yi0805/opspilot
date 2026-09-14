import copy
import json
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from app.db.seed import seed_demo_data
from app.services.llm_agent import (
    FINAL_OUTPUT_SCHEMA,
    MAX_TOOL_CALLS,
    SYSTEM_INSTRUCTIONS,
    BusinessQuestionResult,
    LLMProviderError,
    answer_business_question,
)
from app.services.llm_tools import TOOL_DEFINITIONS


class FakeResponses:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(copy.deepcopy(kwargs))
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = FakeResponses(responses)


def function_call(name: str, arguments: dict[str, object], call_id: str) -> object:
    return SimpleNamespace(
        output=[
            SimpleNamespace(
                type="function_call",
                name=name,
                arguments=json.dumps(arguments),
                call_id=call_id,
            )
        ]
    )


def no_tool_response() -> object:
    return SimpleNamespace(output=[])


def structured_final(
    answer: str, recommendation: str | None = None, limitations: list[str] | None = None
) -> object:
    return SimpleNamespace(
        output_text=json.dumps(
            {
                "answer": answer,
                "recommendation": recommendation,
                "limitations": limitations or [],
            }
        )
    )


def test_agent_executes_two_real_tools_and_preserves_accumulated_context(session: Session) -> None:
    seed_demo_data(session)
    question = "Compare FW-100 sales and inventory. Is there a replenishment risk?"
    sales_call = function_call(
        "query_sales",
        {"sku": "FW-100", "start_date": None, "end_date": None},
        "sales_1",
    )
    inventory_call = function_call("query_inventory", {"sku": "FW-100"}, "inventory_1")
    client = FakeClient(
        [
            sales_call,
            inventory_call,
            no_tool_response(),
            structured_final(
                "FW-100 sold 310 units and has 22 units available.",
                "Prioritize replenishment monitoring for FW-100.",
            ),
        ]
    )

    result = answer_business_question(session, question, client=client)

    assert result == BusinessQuestionResult(
        answer="FW-100 sold 310 units and has 22 units available.",
        recommendation="Prioritize replenishment monitoring for FW-100.",
        evidence=[
            {
                "tool": "query_sales",
                "arguments": {"sku": "FW-100", "start_date": None, "end_date": None},
                "data": [
                    {
                        "sku": "FW-100",
                        "name": "Forest Builder Blocks",
                        "units_sold": 310,
                        "revenue": "12396.90",
                        "gross_profit": "7281.90",
                    }
                ],
                "source": "synthetic_business_data",
            },
            {
                "tool": "query_inventory",
                "arguments": {"sku": "FW-100"},
                "data": [
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
                ],
                "source": "synthetic_business_data",
            },
        ],
    )
    assert len(client.responses.calls) == 4
    for request in client.responses.calls:
        assert request["instructions"] == SYSTEM_INSTRUCTIONS
        assert request["tools"] == list(TOOL_DEFINITIONS)
        assert request["parallel_tool_calls"] is False
        assert request["input"][0] == {"role": "user", "content": question}

    second_input = client.responses.calls[1]["input"]
    assert second_input[1].name == "query_sales"
    assert second_input[-1]["type"] == "function_call_output"
    assert '"units_sold": 310' in second_input[-1]["output"]

    third_input = client.responses.calls[2]["input"]
    assert third_input[3].name == "query_inventory"
    assert third_input[-1]["type"] == "function_call_output"
    assert '"available_stock": 22' in third_input[-1]["output"]

    final_request = client.responses.calls[3]
    assert final_request["tool_choice"] == "none"
    assert final_request["text"] == {"format": FINAL_OUTPUT_SCHEMA}


def test_agent_discards_recommendation_without_tool_evidence(session: Session) -> None:
    client = FakeClient(
        [
            no_tool_response(),
            structured_final(
                "I can help with the available synthetic business data.", "Increase inventory."
            ),
        ]
    )

    result = answer_business_question(session, "What can you help with?", client=client)

    assert result == BusinessQuestionResult(
        answer="I can help with the available synthetic business data.",
        recommendation=None,
        evidence=[],
    )


def test_agent_keeps_single_tool_questions_working(session: Session) -> None:
    seed_demo_data(session)
    client = FakeClient(
        [
            function_call("query_inventory", {"sku": "FW-100"}, "inventory_1"),
            no_tool_response(),
            structured_final("FW-100 has 22 units available."),
        ]
    )

    result = answer_business_question(session, "How much stock is available for FW-100?", client=client)

    assert result.status == "completed"
    assert result.answer == "FW-100 has 22 units available."
    assert result.recommendation is None
    assert len(result.evidence) == 1
    assert result.evidence[0].data[0]["available_stock"] == 22


def test_agent_returns_no_data_evidence_without_fabricating_metrics(session: Session) -> None:
    seed_demo_data(session)
    client = FakeClient(
        [
            function_call("query_inventory", {"sku": "UNKNOWN"}, "inventory_1"),
            no_tool_response(),
            structured_final(
                "No matching inventory data was found for UNKNOWN.",
                "Increase inventory.",
                limitations=["No matching inventory data was returned."],
            ),
        ]
    )

    result = answer_business_question(session, "What stock is available for UNKNOWN?", client=client)

    assert result.recommendation is None
    assert result.evidence[0].data == []
    assert result.evidence[0].source == "synthetic_business_data"


def test_agent_stops_duplicate_canonical_tool_request(session: Session) -> None:
    seed_demo_data(session)
    client = FakeClient(
        [
            function_call("query_inventory", {"sku": "FW-100"}, "inventory_1"),
            function_call("query_inventory", {"sku": "FW-100"}, "inventory_2"),
        ]
    )

    result = answer_business_question(session, "Check FW-100 inventory", client=client)

    assert result.status == "duplicate_tool_call"
    assert len(result.evidence) == 1
    assert len(client.responses.calls) == 2


def test_agent_stops_at_maximum_tool_calls(session: Session) -> None:
    seed_demo_data(session)
    client = FakeClient(
        [
            function_call("query_inventory", {"sku": "FW-100"}, "inventory_1"),
            function_call(
                "query_sales",
                {"sku": "FW-100", "start_date": None, "end_date": None},
                "sales_1",
            ),
            function_call("query_campaigns", {"sku": "FW-100", "status": None}, "campaigns_1"),
            function_call("get_product_details", {"sku": "FW-100"}, "product_1"),
            function_call("query_inventory", {"sku": "HB-500"}, "inventory_2"),
        ]
    )

    result = answer_business_question(session, "Keep checking products", client=client)

    assert result.status == "tool_limit_reached"
    assert len(result.evidence) == MAX_TOOL_CALLS
    assert len(client.responses.calls) == MAX_TOOL_CALLS + 1
    assert all(record.arguments.get("sku") != "HB-500" for record in result.evidence)


def test_agent_returns_controlled_tool_error_for_unknown_tool(session: Session) -> None:
    client = FakeClient([function_call("delete_everything", {}, "bad_1")])

    result = answer_business_question(session, "Delete everything", client=client)

    assert result.status == "tool_error"
    assert result.evidence == []
    assert "Unsupported tool" in result.answer


def test_agent_returns_controlled_tool_error_when_dispatch_fails(
    monkeypatch: pytest.MonkeyPatch, session: Session
) -> None:
    def failed_dispatch(_: Session, __: str, ___: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr("app.services.llm_agent.dispatch_tool", failed_dispatch)
    client = FakeClient([function_call("query_inventory", {"sku": "FW-100"}, "inventory_1")])

    result = answer_business_question(session, "Check FW-100 inventory", client=client)

    assert result.status == "tool_error"
    assert result.evidence == []
    assert result.answer == "I could not run the requested business tool because the data query failed."


def test_agent_rejects_malformed_structured_final_response(session: Session) -> None:
    client = FakeClient([no_tool_response(), SimpleNamespace(output_text='{"answer": 42}')])

    with pytest.raises(LLMProviderError, match="invalid structured final answer"):
        answer_business_question(session, "What can you help with?", client=client)
