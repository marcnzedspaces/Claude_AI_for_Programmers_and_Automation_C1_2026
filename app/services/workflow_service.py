from dataclasses import dataclass
from datetime import datetime, timezone
from time import perf_counter

from app.repositories.faq_repository import FAQRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.common import Priority, TicketStatus
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketResponse,
)
from app.schemas.usage import AIUsage
from app.schemas.workflow import (
    ProcessTicketRequest,
    WorkflowStep,
)
from app.services.analysis_service import AnalysisService
from app.services.response_service import ResponseService
from app.services.ticket_service import TicketService


@dataclass(frozen=True)
class WorkflowProcessResult:
    ticket: TicketResponse
    executed_steps: list[WorkflowStep]
    analysis_usage: AIUsage
    response_usage: AIUsage


class WorkflowService:
    def __init__(
        self,
        *,
        analysis_service: AnalysisService,
        response_service: ResponseService,
        ticket_service: TicketService,
        order_repository: OrderRepository,
        faq_repository: FAQRepository,
    ) -> None:
        self.analysis_service = analysis_service
        self.response_service = response_service
        self.ticket_service = ticket_service
        self.order_repository = order_repository
        self.faq_repository = faq_repository

    async def process(
        self,
        request: ProcessTicketRequest,
    ) -> WorkflowProcessResult:
        steps: list[WorkflowStep] = []

        analysis_started = perf_counter()
        analysis_result = await self.analysis_service.analyse(
            request.message
        )
        analysis_latency_ms = int(
            (perf_counter() - analysis_started) * 1000
        )
        steps.append(WorkflowStep.ANALYSIS)

        analysis = analysis_result.data
        order_context = None
        faq_context = []

        requires_human_review = (
            analysis.needs_human_review
            or analysis.priority == Priority.URGENT
        )

        if analysis.needs_order_lookup:
            if request.order_id:
                order_context = (
                    await self.order_repository.get_order_for_customer(
                        request.customer_id,
                        request.order_id,
                    )
                )
                steps.append(WorkflowStep.ORDER_LOOKUP)

            if order_context is None:
                requires_human_review = True

        if analysis.needs_faq_lookup:
            faq_context = await self.faq_repository.search(
                analysis.faq_query or request.message,
                limit=3,
            )
            steps.append(WorkflowStep.FAQ_LOOKUP)

            if not faq_context:
                requires_human_review = True

        ticket = await self.ticket_service.create(
            TicketCreateRequest(
                customer_id=request.customer_id,
                order_id=request.order_id,
                message=request.message,
            ),
            analysis,
        )
        steps.append(WorkflowStep.DATABASE_INSERT)

        response_started = perf_counter()
        # Generate a customer-facing draft using any trusted context retrieved.
        response_result = (
            await self.response_service.generate_draft(
                request.message,
                order_context=order_context,
                faq_context=faq_context,
            )
        )
        response_latency_ms = int(
            (perf_counter() - response_started) * 1000
        )
        steps.append(WorkflowStep.RESPONSE_GENERATION)

        final_status = (
            TicketStatus.NEEDS_HUMAN_REVIEW
            if requires_human_review
            else TicketStatus.PROCESSED
        )
        # Combine the original ticket with all context and generated results.
        updated_ticket = TicketResponse.model_validate(
            {
                **ticket.model_dump(mode="python"),
                "order_context": order_context,
                "faq_context": faq_context,
                "draft_response": response_result.text,
                "status": final_status,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        # Persist the completed workflow state back to the database.

        updated_ticket = await self.ticket_service.save(
            updated_ticket
        )
        steps.append(WorkflowStep.DATABASE_UPDATE)

        # Return the completed ticket, workflow history, and both Claude usages.
        return WorkflowProcessResult(
            ticket=updated_ticket,
            executed_steps=steps,
            analysis_usage=AIUsage(
                model=analysis_result.model,
                input_tokens=analysis_result.input_tokens,
                output_tokens=analysis_result.output_tokens,
                latency_ms=analysis_latency_ms,
            ),
            response_usage=AIUsage(
                model=response_result.model,
                input_tokens=response_result.input_tokens,
                output_tokens=response_result.output_tokens,
                latency_ms=response_latency_ms,
            ),
        )
