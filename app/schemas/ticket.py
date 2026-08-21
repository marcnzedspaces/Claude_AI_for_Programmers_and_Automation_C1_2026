from datetime import datetime

from pydantic import Field

from app.schemas.ai import TicketAnalysis
from app.schemas.common import (
    StrictModel,
    TicketStatus,
)
from app.schemas.order import OrderContext
from app.schemas.faq import FAQSource
from app.schemas.order import OrderContext


class TicketCreateRequest(StrictModel):
    # User/application identifiers arrive with the support request.
    customer_id: str = Field(
        min_length=3,
        max_length=50,
    )
    order_id: str | None = Field(
        default=None,
        max_length=50,
    )
    message: str = Field(
        min_length=5,
        max_length=5000,
    )


class TicketResponse(StrictModel):
    # Application-created identity and original request data.
    ticket_id: str
    customer_id: str
    order_id: str | None
    message: str

    # Claude analysis is stored only after it has passed schema validation.
    analysis: TicketAnalysis

    # Trusted enrichment is added later by workflows/tools.
    order_context: OrderContext | None = None
    faq_context: list[FAQSource] = Field(
        default_factory=list,
    )
    draft_response: str | None = None

    # Application-owned workflow state and audit fields.
    status: TicketStatus
    escalation_reason: str | None = None
    processing_error: str | None = None
    created_at: datetime
    updated_at: datetime


class TicketListResponse(StrictModel):
    # Return pagination metadata with the list.
    items: list[TicketResponse]
    total: int = Field(ge=0)
    limit: int = Field(
        ge=1,
        le=100,
    )
    skip: int = Field(ge=0)
