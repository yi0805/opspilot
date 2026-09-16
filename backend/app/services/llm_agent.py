"""Controlled multi-tool Responses API business-question service."""

import json
import logging
import re
from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.services.llm_tools import (
    TOOL_DEFINITIONS,
    ToolDispatchError,
    dispatch_tool,
    validate_tool_arguments,
)

logger = logging.getLogger(__name__)
SAFE_REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}")

SYSTEM_INSTRUCTIONS = (
    "Answer concise, commercially understandable business questions using the supplied "
    "business tools. Use tools for every business-data fact and use multiple tools when "
    "the question needs multiple data sources. Do not invent metrics or claim data that a "
    "tool did not return. Distinguish observations from recommendations, and make a "
    "recommendation only when collected evidence supports it. If evidence is empty or "
    "insufficient, explain that limitation and set recommendation to null. Do not claim "
    "causation from this synthetic data; describe only correlation or association. Do not "
    "reveal hidden reasoning."
)

MAX_TOOL_CALLS = 4
EVIDENCE_SOURCE: Literal["synthetic_business_data"] = "synthetic_business_data"
FINAL_OUTPUT_SCHEMA = {
    "type": "json_schema",
    "name": "business_question_answer",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "recommendation": {"type": ["string", "null"]},
            "limitations": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["answer", "recommendation", "limitations"],
        "additionalProperties": False,
    },
}


class EvidenceRecord(BaseModel):
    tool: str
    arguments: dict[str, Any]
    data: Any
    source: Literal["synthetic_business_data"] = EVIDENCE_SOURCE


class _FinalModelPayload(BaseModel):
    answer: str = Field(min_length=1)
    recommendation: str | None = None
    limitations: list[str] = Field(default_factory=list)


class BusinessQuestionResult(BaseModel):
    answer: str
    recommendation: str | None = None
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    status: Literal["completed", "tool_error", "tool_limit_reached", "duplicate_tool_call"] = (
        "completed"
    )


class LLMConfigurationError(RuntimeError):
    """Raised when local OpenRouter configuration is incomplete."""


class LLMProviderError(RuntimeError):
    """Raised when a provider response cannot be used safely."""


def _log_provider_failure(stage: Literal["reasoning", "final"], error: Exception) -> None:
    """Log only allowlisted scalar metadata from a provider request failure."""
    status_code = getattr(error, "status_code", None)
    if type(status_code) is not int or not 100 <= status_code <= 599:
        status_code = None

    request_id = getattr(error, "request_id", None)
    if (
        type(request_id) is not str
        or SAFE_REQUEST_ID_PATTERN.fullmatch(request_id) is None
    ):
        request_id = None

    logger.warning(
        "OpenRouter request failed stage=%s exception_type=%s status_code=%s request_id=%s",
        stage,
        type(error).__name__,
        status_code,
        request_id,
    )


def _item_value(item: Any, field_name: str) -> Any:
    if isinstance(item, dict):
        return item.get(field_name)
    return getattr(item, field_name, None)


def _function_calls(response: Any) -> list[Any]:
    return [
        item
        for item in (_item_value(response, "output") or [])
        if _item_value(item, "type") == "function_call"
    ]


def _output_text(response: Any) -> str:
    output_text = _item_value(response, "output_text")
    if not isinstance(output_text, str) or not output_text.strip():
        raise LLMProviderError("The model did not return a usable answer.")
    return output_text.strip()


def _final_payload(response: Any) -> _FinalModelPayload:
    try:
        payload = json.loads(_output_text(response))
        return _FinalModelPayload.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as error:
        raise LLMProviderError("The model returned an invalid structured final answer.") from error


def _response_output(response: Any) -> list[Any]:
    output = _item_value(response, "output") or []
    if not isinstance(output, list):
        raise LLMProviderError("The model returned an invalid response output.")
    return output


def _has_supporting_evidence(evidence: list[EvidenceRecord]) -> bool:
    """Return whether an executed business tool returned non-empty data."""
    return any(bool(record.data) for record in evidence)


def _create_reasoning_response(
    client: OpenAI | Any, settings: Settings, input_messages: list[Any]
) -> Any:
    try:
        return client.responses.create(
            model=settings.openrouter_model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=input_messages,
            tools=list(TOOL_DEFINITIONS),  # type: ignore[arg-type]
            parallel_tool_calls=False,
        )
    except Exception as error:
        _log_provider_failure("reasoning", error)
        raise LLMProviderError("OpenRouter could not process the business question.") from error


def _create_final_response(client: OpenAI | Any, settings: Settings, input_messages: list[Any]) -> Any:
    try:
        return client.responses.create(  # type: ignore[call-overload]
            model=settings.openrouter_model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=input_messages,
            tools=list(TOOL_DEFINITIONS),
            parallel_tool_calls=False,
            tool_choice="none",
            text={"format": FINAL_OUTPUT_SCHEMA},
        )
    except Exception as error:
        _log_provider_failure("final", error)
        raise LLMProviderError("OpenRouter could not produce a final business answer.") from error


def answer_business_question(
    session: Session,
    question: str,
    *,
    client: OpenAI | Any | None = None,
    settings: Settings | None = None,
) -> BusinessQuestionResult:
    """Answer a question through a capped, sequential allowlisted-tool workflow."""
    configured_settings = settings or get_settings()
    if client is None:
        if not configured_settings.openrouter_api_key:
            raise LLMConfigurationError("OPENROUTER_API_KEY is not configured.")
        client = OpenAI(
            api_key=configured_settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    input_messages: list[Any] = [{"role": "user", "content": question}]
    evidence: list[EvidenceRecord] = []
    executed_calls: set[str] = set()

    while True:
        response = _create_reasoning_response(client, configured_settings, input_messages)
        response_output = _response_output(response)
        function_calls = _function_calls(response)
        if len(function_calls) > 1:
            raise LLMProviderError("The model returned multiple tool calls in one turn.")

        input_messages.extend(response_output)
        if not function_calls:
            final_response = _create_final_response(client, configured_settings, input_messages)
            final_payload = _final_payload(final_response)
            return BusinessQuestionResult(
                answer=final_payload.answer,
                recommendation=(
                    final_payload.recommendation if _has_supporting_evidence(evidence) else None
                ),
                evidence=evidence,
            )

        if len(evidence) >= MAX_TOOL_CALLS:
            return BusinessQuestionResult(
                answer=(
                    "I could not complete the analysis because it exceeded the maximum "
                    "number of business-tool calls."
                ),
                evidence=evidence,
                status="tool_limit_reached",
            )

        function_call = function_calls[0]
        tool_name = _item_value(function_call, "name")
        arguments = _item_value(function_call, "arguments")
        call_id = _item_value(function_call, "call_id")
        if not isinstance(tool_name, str) or not isinstance(call_id, str):
            raise LLMProviderError("The model returned an invalid tool call.")

        try:
            canonical_arguments = validate_tool_arguments(tool_name, arguments)
        except ToolDispatchError as error:
            return BusinessQuestionResult(
                answer=f"I could not run the requested business tool: {error}",
                evidence=evidence,
                status="tool_error",
            )

        call_signature = json.dumps(
            {"tool": tool_name, "arguments": canonical_arguments}, sort_keys=True, separators=(",", ":")
        )
        if call_signature in executed_calls:
            return BusinessQuestionResult(
                answer="I could not complete the analysis because the same business-tool request repeated.",
                evidence=evidence,
                status="duplicate_tool_call",
            )

        try:
            tool_result = dispatch_tool(session, tool_name, canonical_arguments)
        except ToolDispatchError as error:
            return BusinessQuestionResult(
                answer=f"I could not run the requested business tool: {error}",
                evidence=evidence,
                status="tool_error",
            )
        except Exception:
            return BusinessQuestionResult(
                answer="I could not run the requested business tool because the data query failed.",
                evidence=evidence,
                status="tool_error",
            )

        executed_calls.add(call_signature)
        evidence.append(
            EvidenceRecord(
                tool=tool_result["tool"],
                arguments=tool_result["arguments"],
                data=tool_result["data"],
            )
        )
        input_messages.append(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(tool_result),
            }
        )
