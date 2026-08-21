from pydantic import Field

from app.schemas.common import (
    StrictModel,
    TicketCategory,
)
from app.schemas.usage import AIUsage


class FAQSource(StrictModel):
    # Approved source data retrieved from MongoDB.
    faq_id: str = Field(min_length=3, max_length=50,)
    category: TicketCategory
    question: str = Field(min_length=3, max_length=500)
    answer: str = Field(min_length=3, max_length=2000)


class FAQAnswerDecision(StrictModel):
    # Claude must state both its answer and whether the supplied sources support it.
    answer: str = Field(
        min_length=1,
        max_length=2000,
    )
    supported_by_sources: bool


class FAQAskRequest(StrictModel):
    question: str = Field(
        min_length=5,
        max_length=1000,
    )


class FAQAskResponse(StrictModel):
    answer: str = Field(
        min_length=1,
        max_length=2000,
    )
    sources: list[FAQSource] = Field(
        default_factory=list,
    )
    requires_human_review: bool
    usage: AIUsage | None = None
