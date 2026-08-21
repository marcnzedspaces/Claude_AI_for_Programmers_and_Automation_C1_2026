from dataclasses import dataclass
from time import perf_counter

from app.repositories.faq_repository import FAQRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.ai import GenerateResponseRequest
from app.services.response_service import ResponseService


@dataclass(frozen=True)
class GenerateResponseResult:
    draft_response: str
    order_id_used: str | None
    faq_ids_used: list[str]
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class GenerateResponseService:
    def __init__(
        self,
        *,
        response_service: ResponseService,
        order_repository: OrderRepository,
        faq_repository: FAQRepository,
    ) -> None:
        self.response_service = response_service
        self.order_repository = order_repository
        self.faq_repository = faq_repository

    async def generate(
        self,
        request: GenerateResponseRequest,
    ) -> GenerateResponseResult:
        order_context = None

        if request.order_id and request.customer_id:
            order_context = (
                await self.order_repository.get_order_for_customer(
                    request.customer_id,
                    request.order_id,
                )
            )

        faq_context = await self.faq_repository.get_by_ids(
            request.faq_ids
        )

        started = perf_counter()

        claude_result = await self.response_service.generate_draft(
            request.customer_message,
            order_context=order_context,
            faq_context=faq_context,
        )

        latency_ms = int(
            (perf_counter() - started) * 1000
        )

        return GenerateResponseResult(
            draft_response=claude_result.text,
            order_id_used=(
                order_context.order_id
                if order_context
                else None
            ),
            faq_ids_used=[
                faq.faq_id
                for faq in faq_context
            ],
            model=claude_result.model,
            input_tokens=claude_result.input_tokens,
            output_tokens=claude_result.output_tokens,
            latency_ms=latency_ms,
        )
