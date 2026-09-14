from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes import agent as agent_route
from app.main import app
from app.services.llm_agent import (
    BusinessQuestionResult,
    LLMConfigurationError,
    LLMProviderError,
)


@pytest.fixture
def client(session: Session) -> Generator[TestClient]:
    app.dependency_overrides[agent_route.get_db] = lambda: session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_query_agent_returns_the_business_result_contract(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_result = BusinessQuestionResult(
        answer="FW-100 stock is low.",
        recommendation="Review replenishment.",
        evidence=[
            {
                "tool": "query_inventory",
                "arguments": {"sku": "FW-100"},
                "data": [{"available_stock": 22}],
                "source": "synthetic_business_data",
            }
        ],
    )

    def fake_answer(_: Session, question: str) -> BusinessQuestionResult:
        assert question == "How much stock is available for FW-100?"
        return expected_result

    monkeypatch.setattr(agent_route, "answer_business_question", fake_answer)

    response = client.post("/api/agent/query", json={"question": "How much stock is available for FW-100?"})

    assert response.status_code == 200
    assert response.json() == expected_result.model_dump(mode="json")


@pytest.mark.parametrize("question", ["", "   "])
def test_query_agent_rejects_blank_questions(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, question: str
) -> None:
    def agent_must_not_run(_: Session, __: str) -> BusinessQuestionResult:
        raise AssertionError("The agent service must not run for invalid input.")

    monkeypatch.setattr(agent_route, "answer_business_question", agent_must_not_run)

    assert client.post("/api/agent/query", json={"question": question}).status_code == 422


def test_query_agent_rejects_a_question_longer_than_500_characters(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def agent_must_not_run(_: Session, __: str) -> BusinessQuestionResult:
        raise AssertionError("The agent service must not run for invalid input.")

    monkeypatch.setattr(agent_route, "answer_business_question", agent_must_not_run)

    assert client.post("/api/agent/query", json={"question": "x" * 501}).status_code == 422


def test_query_agent_maps_missing_configuration_to_a_safe_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing_configuration(_: Session, __: str) -> BusinessQuestionResult:
        raise LLMConfigurationError("do not expose this detail")

    monkeypatch.setattr(agent_route, "answer_business_question", missing_configuration)

    response = client.post("/api/agent/query", json={"question": "What stock is available?"})

    assert response.status_code == 503
    assert response.json() == {"detail": "The AI service is not configured."}


def test_query_agent_maps_provider_failure_to_a_safe_502(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def provider_failure(_: Session, __: str) -> BusinessQuestionResult:
        raise LLMProviderError("do not expose this detail")

    monkeypatch.setattr(agent_route, "answer_business_question", provider_failure)

    response = client.post("/api/agent/query", json={"question": "What stock is available?"})

    assert response.status_code == 502
    assert response.json() == {"detail": "The AI service is temporarily unavailable."}
