from enum import Enum
from typing import Any

from pydantic import Field

from app.schemas.common import StrictModel
from app.schemas.ticket import TicketResponse
from app.schemas.usage import AIUsage


class ToolName(str, Enum):
    GET_ORDER_STATUS = "get_order_status"
    SEARCH_FAQ = "search_faq"
    ESCALATE_TICKET = "escalate_ticket"


class GetOrderStatusArgs(StrictModel):
    order_id: str = Field(
        min_length=3,
        max_length=50,
    )


class SearchFAQArgs(StrictModel):
    query: str = Field(
        min_length=3,
        max_length=200,
    )


class EscalateTicketArgs(StrictModel):
    reason: str = Field(
        min_length=5,
        max_length=300,
    )


class AgentSupportRequest(StrictModel):
    customer_id: str = Field(
        min_length=3,
        max_length=50,
    )
    order_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )
    message: str = Field(
        min_length=5,
        max_length=5000,
    )


class ToolExecutionAudit(StrictModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    success: bool
    result_summary: str = Field(
        min_length=1,
        max_length=500,
    )


class AgentSupportResponse(StrictModel):
    ticket: TicketResponse
    final_response: str = Field(
        min_length=1,
        max_length=5000,
    )
    tool_calls: list[ToolExecutionAudit] = Field(
        default_factory=list,
    )
    iterations: int = Field(
        ge=1,
        le=4,
    )
    analysis_usage: AIUsage
    agent_usage: AIUsage
