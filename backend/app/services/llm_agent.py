"""Single-cycle Responses API business-question service."""

import json
from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.services.llm_tools import TOOL_DEFINITIONS, ToolDispatchError, dispatch_tool


SYSTEM_INSTRUCTIONS = (
    "Answer concise business questions using the supplied business tools. "
    "Use tools for business-data facts; do not invent metrics. "
    "If the data cannot answer, say so plainly. "
    "This interaction supports one tool call only."
)


class BusinessQuestionResult(BaseModel):
    answer: str
    tool_used: str | None = None
    tool_arguments: dict[str, Any] | None = None
    status: Literal["completed", "tool_error", "unsupported_multi_tool"] = "completed"


class LLMConfigurationError(RuntimeError):
    """Raised when local OpenAI configuration is incomplete."""


class LLMProviderError(RuntimeError):
    """Raised when a provider response cannot be used safely."""


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


def answer_business_question(
    session: Session,
    question: str,
    *,
    client: OpenAI | Any | None = None,
    settings: Settings | None = None,
) -> BusinessQuestionResult:
    """Answer one question with at most one allowlisted business-tool execution."""
    configured_settings = settings or get_settings()
    if client is None:
        if not configured_settings.openai_api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is not configured.")
        client = OpenAI(api_key=configured_settings.openai_api_key)

    try:
        initial_response = client.responses.create(
            model=configured_settings.openai_model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=question,
            tools=list(TOOL_DEFINITIONS),
            parallel_tool_calls=False,
        )
    except Exception as error:
        raise LLMProviderError("OpenAI could not process the business question.") from error

    function_calls = _function_calls(initial_response)
    if len(function_calls) > 1:
        return BusinessQuestionResult(
            answer="This question needs multiple business tools, which is not supported yet.",
            status="unsupported_multi_tool",
        )
    if not function_calls:
        return BusinessQuestionResult(answer=_output_text(initial_response))

    function_call = function_calls[0]
    tool_name = _item_value(function_call, "name")
    arguments = _item_value(function_call, "arguments")
    call_id = _item_value(function_call, "call_id")
    if not isinstance(tool_name, str) or not isinstance(call_id, str):
        raise LLMProviderError("The model returned an invalid tool call.")

    try:
        tool_result = dispatch_tool(session, tool_name, arguments)
    except ToolDispatchError as error:
        return BusinessQuestionResult(
            answer=f"I could not run the requested business tool: {error}",
            tool_used=tool_name,
            status="tool_error",
        )

    try:
        final_response = client.responses.create(
            model=configured_settings.openai_model,
            input=[
                *(_item_value(initial_response, "output") or []),
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(tool_result),
                },
            ],
        )
    except Exception as error:
        raise LLMProviderError("OpenAI could not produce a final business answer.") from error

    return BusinessQuestionResult(
        answer=_output_text(final_response),
        tool_used=tool_name,
        tool_arguments=tool_result["arguments"],
    )
