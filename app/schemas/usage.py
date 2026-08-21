from datetime import datetime
from enum import Enum

from pydantic import Field

from app.schemas.common import StrictModel


class AIOperation(str, Enum):
    TICKET_ANALYSIS = "ticket_analysis"
    RESPONSE_GENERATION = "response_generation"
    FAQ_ANSWER = "faq_answer"
    AGENT_DECISION = "agent_decision"


class AIUsage(StrictModel):
    model: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)


class AIUsageLog(StrictModel):
    usage_id: str = Field(min_length=3, max_length=50)
    request_id: str = Field(min_length=3, max_length=100)
    ticket_id: str | None = Field(
        default=None,
        max_length=50,
    )
    operation: AIOperation
    model: str = Field(min_length=1, max_length=100)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    created_at: datetime


class UsageSummary(StrictModel):
    total_calls: int = Field(ge=0)
    total_input_tokens: int = Field(ge=0)
    total_output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    average_latency_ms: float = Field(ge=0)


class UsageResponse(StrictModel):
    summary: UsageSummary
    items: list[AIUsageLog]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    skip: int = Field(ge=0)
