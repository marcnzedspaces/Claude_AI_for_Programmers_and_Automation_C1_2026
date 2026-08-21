from fastapi import APIRouter, Request, status

from app.database import get_database
from app.repositories.faq_repository import FAQRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.usage_repository import UsageRepository
from app.schemas.usage import AIOperation
from app.schemas.workflow import (
    ProcessTicketRequest,
    ProcessTicketResponse,
)
from app.services.analysis_service import AnalysisService
from app.services.claude_service import ClaudeService
from app.services.response_service import ResponseService
from app.services.ticket_service import TicketService
from app.services.usage_service import UsageService
from app.services.workflow_service import WorkflowService


router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
)


@router.post(
    "/process-ticket",
    response_model=ProcessTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def process_ticket(
    request: ProcessTicketRequest,
    http_request: Request,
) -> ProcessTicketResponse:
    database = get_database()
    claude_service = ClaudeService()
    usage_service = UsageService(
        UsageRepository(database)
    )

    service = WorkflowService(
        analysis_service=AnalysisService(claude_service),
        response_service=ResponseService(claude_service),
        ticket_service=TicketService(
            TicketRepository(database)
        ),
        order_repository=OrderRepository(database),
        faq_repository=FAQRepository(database),
    )

    try:
        result = await service.process(request)
    finally:
        await claude_service.close()

    await usage_service.safe_record(
        request_id=http_request.state.request_id,
        operation=AIOperation.TICKET_ANALYSIS,
        usage=result.analysis_usage,
        ticket_id=result.ticket.ticket_id,
    )
    await usage_service.safe_record(
        request_id=http_request.state.request_id,
        operation=AIOperation.RESPONSE_GENERATION,
        usage=result.response_usage,
        ticket_id=result.ticket.ticket_id,
    )

    return ProcessTicketResponse(
        ticket=result.ticket,
        executed_steps=result.executed_steps,
        analysis_usage=result.analysis_usage,
        response_usage=result.response_usage,
    )
