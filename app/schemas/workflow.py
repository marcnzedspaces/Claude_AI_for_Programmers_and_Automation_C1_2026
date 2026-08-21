from enum import Enum

from pydantic import Field

from app.schemas.common import StrictModel
from app.schemas.ticket import TicketResponse
from app.schemas.usage import AIUsage


# Named steps make deterministic orchestration visible.
class WorkflowStep(str, Enum):
    ANALYSIS = "analysis"
    ORDER_LOOKUP = "order_lookup"
    FAQ_LOOKUP = "faq_lookup"
    DATABASE_INSERT = "database_insert"
    RESPONSE_GENERATION = "response_generation"
    DATABASE_UPDATE = "database_update"


class ProcessTicketRequest(StrictModel):
    customer_id: str = Field(
        min_length=3,
        max_length=50,
    )

    # Not every support request has an order.
    order_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )
    message: str = Field(
        min_length=5,
        max_length=5000,
    )


class ProcessTicketResponse(StrictModel):
    ticket: TicketResponse

    # debugging field showing which deterministic branches ran.
    executed_steps: list[WorkflowStep]

    # Keep the two AI operations separate.
    analysis_usage: AIUsage
    response_usage: AIUsage
