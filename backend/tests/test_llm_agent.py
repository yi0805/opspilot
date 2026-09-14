from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes import agent as agent_route
from app.db.seed import seed_demo_data
from app.main import app
from app.services.llm_agent import (
    BusinessQuestionResult,
    LLMConfigurationError,
    SYSTEM_INSTRUCTIONS,
    answer_business_question,
)
from app.services.llm_tools import TOOL_DEFINITIONS


class FakeResponses:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = FakeResponses(responses)


def test_agent_executes_one_real_tool_then_returns_model_answer(session: Session) -> None:
    seed_demo_data(session)
    question = "How much stock is available for FW-100?"
    initial = SimpleNamespace(
        output=[
            SimpleNamespace(
                type="function_call",
                name="query_inventory",
                arguments='{"sku":"FW-100"}',
                call_id="call_123",
            )
        ]
    )
    final = SimpleNamespace(output_text="FW-100 has 22 units available.")
    client = FakeClient([initial, final])

    result = answer_business_question(session, question, client=client)

    assert result == BusinessQuestionResult(
        answer="FW-100 has 22 units available.",
        tool_used="query_inventory",
        tool_arguments={"sku": "FW-100"},
    )
    assert len(client.responses.calls) == 2
    assert client.responses.calls[0]["parallel_tool_calls"] is False
    final_request = client.responses.calls[1]
    final_input = final_request["input"]
    assert final_input[0] == {"role": "user", "content": question}
    assert initial.output[0] in final_input
    tool_output = final_input[-1]
    assert tool_output["type"] == "function_call_output"
    assert '"available_stock": 22' in tool_output["output"]
    assert final_request["instructions"] == SYSTEM_INSTRUCTIONS
    assert final_request["tools"] == list(TOOL_DEFINITIONS)
    assert final_request["parallel_tool_calls"] is False
    assert final_request["tool_choice"] == "none"


def test_agent_returns_controlled_result_for_multiple_tool_calls(session: Session) -> None:
    response = SimpleNamespace(
        output=[
            SimpleNamespace(type="function_call", name="query_inventory", arguments="{}", call_id="first"),
            SimpleNamespace(type="function_call", name="query_sales", arguments="{}", call_id="second"),
        ]
    )
    client = FakeClient([response])

    result = answer_business_question(session, "Compare inventory and sales", client=client)

    assert result.status == "unsupported_multi_tool"
    assert len(client.responses.calls) == 1


def test_agent_query_endpoint_rejects_blank_or_missing_questions() -> None:
    client = TestClient(app)

    assert client.post("/api/agent/query", json={"question": "   "}).status_code == 422
    assert client.post("/api/agent/query", json={}).status_code == 422


def test_agent_query_endpoint_returns_controlled_configuration_error(monkeypatch: object) -> None:
    def missing_configuration(_: Session, __: str) -> BusinessQuestionResult:
        raise LLMConfigurationError("OPENAI_API_KEY is not configured.")

    monkeypatch.setattr(agent_route, "answer_business_question", missing_configuration)
    client = TestClient(app)

    response = client.post("/api/agent/query", json={"question": "What stock is available?"})

    assert response.status_code == 503
    assert response.json() == {"detail": "OPENAI_API_KEY is not configured."}


def test_agent_query_endpoint_returns_structured_service_result(
    monkeypatch: object, session: Session
) -> None:
    def fake_answer(_: Session, __: str) -> BusinessQuestionResult:
        return BusinessQuestionResult(answer="FW-100 has 22 units available.", tool_used="query_inventory")

    monkeypatch.setattr(agent_route, "answer_business_question", fake_answer)
    app.dependency_overrides[agent_route.get_db] = lambda: session
    try:
        response = TestClient(app).post(
            "/api/agent/query", json={"question": "How much stock is available for FW-100?"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "answer": "FW-100 has 22 units available.",
        "tool_used": "query_inventory",
        "tool_arguments": None,
        "status": "completed",
    }
