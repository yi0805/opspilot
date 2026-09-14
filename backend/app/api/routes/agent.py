from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.llm_agent import (
    BusinessQuestionResult,
    LLMConfigurationError,
    LLMProviderError,
    answer_business_question,
)

router = APIRouter()


class AgentQueryRequest(BaseModel):
    question: str = Field(max_length=500)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be blank")
        return value


def get_db() -> Generator[Session]:
    with SessionLocal() as session:
        yield session


@router.post("/agent/query", response_model=BusinessQuestionResult)
def query_agent(
    request: AgentQueryRequest, session: Session = Depends(get_db)  # noqa: B008
) -> BusinessQuestionResult:
    """Answer one business question through the constrained tool-calling service."""
    try:
        return answer_business_question(session, request.question)
    except LLMConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is not configured.",
        ) from error
    except LLMProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service is temporarily unavailable.",
        ) from error
