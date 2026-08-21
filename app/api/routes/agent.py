# This route composes the bounded agent and records request-correlated AI usage.
from fastapi import APIRouter, Request, status

# Use the shared database dependency; routes/services do not create hidden MongoDB clients.
from app.database import get_database
from app.repositories.faq_repository import FAQRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.usage_repository import UsageRepository
from app.schemas.agent import (
    AgentSupportRequest,
    AgentSupportResponse,
)
from app.schemas.usage import AIOperation
from app.services.agent_service import AgentService
from app.services.analysis_service import AnalysisService
from app.services.claude_service import ClaudeService
from app.services.ticket_service import TicketService
from app.services.usage_service import UsageService


# Group related endpoints under one router so the feature can be registered as a unit.
router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)


# Register a POST endpoint while the function below retains the actual request-handling logic.
@router.post(
    "/support",
    response_model=AgentSupportResponse,
    status_code=status.HTTP_201_CREATED,
)
# Keep `agent_support()` focused on this layer's responsibility instead of mixing unrelated concerns.
async def agent_support(
    request: AgentSupportRequest,
    http_request: Request,
) -> AgentSupportResponse:
    # Use the shared application database handle instead of creating a new MongoDB client inside the request.
    database = get_database()
    # Create the low-level Claude integration dependency for this request.
    claude_service = ClaudeService()

    ticket_service = TicketService(
        TicketRepository(database)
    )
    usage_service = UsageService(
        UsageRepository(database)
    )

    service = AgentService(
        claude_service=claude_service,
        analysis_service=AnalysisService(claude_service),
        ticket_service=ticket_service,
        order_repository=OrderRepository(database),
        faq_repository=FAQRepository(database),
    )

    try:
        result = await service.support(request)
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
        operation=AIOperation.AGENT_DECISION,
        usage=result.agent_usage,
        ticket_id=result.ticket.ticket_id,
    )

    return AgentSupportResponse(
        ticket=result.ticket,
        final_response=result.final_response,
        tool_calls=result.tool_calls,
        iterations=result.iterations,
        analysis_usage=result.analysis_usage,
        agent_usage=result.agent_usage,
    )
