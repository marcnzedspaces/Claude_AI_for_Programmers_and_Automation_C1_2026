from pydantic import Field, model_validator

from app.schemas.common import (
    Priority,
    Sentiment,
    StrictModel,
    TicketCategory,
)
from app.schemas.usage import AIUsage


class AnalyseRequest(StrictModel):
    message: str = Field(min_length=5, max_length=5000)


class TicketAnalysis(StrictModel):
    summary: str = Field(min_length=5, max_length=300)
    category: TicketCategory
    sentiment: Sentiment
    priority: Priority

    needs_order_lookup: bool
    needs_faq_lookup: bool
    needs_human_review: bool
    faq_query: str | None = Field(default=None, max_length=200)
    human_review_reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_dependencies(self) -> "TicketAnalysis":
        if self.needs_faq_lookup and not self.faq_query:
            raise ValueError(
                "faq_query is required when needs_faq_lookup is true"
            )

        if self.needs_human_review and not self.human_review_reason:
            raise ValueError(
                "human_review_reason is required when needs_human_review is true"
            )

        return self


class AnalyseResponse(StrictModel):
    analysis: TicketAnalysis
    usage: AIUsage


class GenerateResponseRequest(StrictModel):
    # Customer text remains untrusted input.
    customer_message: str = Field(min_length=5, max_length=5000)

    # Identifiers let the application retrieve trusted order context.
    customer_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )
    order_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )

    # Caller may request a small set of approved FAQ records by ID.
    faq_ids: list[str] = Field(
        default_factory=list,
        max_length=3,
    )

    @model_validator(mode="after")
    def validate_order_context(self) -> "GenerateResponseRequest":
        # An order lookup cannot be safely scoped without a customer ID.
        if self.order_id and not self.customer_id:
            raise ValueError(
                "customer_id is required when order_id is provided"
            )

        return self


class ResponseContextUsed(StrictModel):
    # Make trusted context available to the app for logging and debugging purposes. This is not sent to Claude.
    # Show exactly which trusted context the application used.
    order_id: str | None = None
    faq_ids: list[str] = Field(default_factory=list)


class GenerateResponseResponse(StrictModel):
    draft_response: str = Field(
        min_length=1,
        max_length=5000,
    )
    context_used: ResponseContextUsed
    usage: AIUsage
