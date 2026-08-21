from time import perf_counter

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    status as http_status,
)

from app.database import get_database
from app.repositories.ticket_repository import TicketRepository
from app.repositories.usage_repository import UsageRepository
from app.schemas.common import TicketCategory, TicketStatus
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketListResponse,
    TicketResponse,
)
from app.schemas.usage import AIOperation, AIUsage
from app.services.analysis_service import AnalysisService
from app.services.claude_service import ClaudeService
from app.services.ticket_service import TicketService
from app.services.usage_service import UsageService


router = APIRouter(
    prefix="/tickets",
    tags=["tickets"],
)


@router.post(
    "",
    response_model=TicketResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_ticket(
    request: TicketCreateRequest,
    http_request: Request,
) -> TicketResponse:
    database = get_database()
    ticket_service = TicketService(
        TicketRepository(database)
    )
    usage_service = UsageService(
        UsageRepository(database)
    )

    claude_service = ClaudeService()
    analysis_service = AnalysisService(claude_service)

    started = perf_counter()

    try:
        analysis_result = await analysis_service.analyse(
            request.message
        )
    finally:
        await claude_service.close()

    latency_ms = int(
        (perf_counter() - started) * 1000
    )

    ticket = await ticket_service.create(
        request,
        analysis_result.data,
    )

    await usage_service.safe_record(
        request_id=http_request.state.request_id,
        operation=AIOperation.TICKET_ANALYSIS,
        usage=AIUsage(
            model=analysis_result.model,
            input_tokens=analysis_result.input_tokens,
            output_tokens=analysis_result.output_tokens,
            latency_ms=latency_ms,
        ),
        ticket_id=ticket.ticket_id,
    )

    return ticket


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
async def get_ticket(
    ticket_id: str,
) -> TicketResponse:
    database = get_database()
    ticket_service = TicketService(
        TicketRepository(database)
    )

    ticket = await ticket_service.get(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Ticket not found.",
        )

    return ticket


@router.get(
    "",
    response_model=TicketListResponse,
)
async def list_tickets(
    customer_id: str | None = Query(
        default=None,
        min_length=3,
        max_length=50,
    ),
    status: TicketStatus | None = Query(
        default=None,
    ),
    category: TicketCategory | None = Query(
        default=None,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
) -> TicketListResponse:
    database = get_database()
    ticket_service = TicketService(
        TicketRepository(database)
    )

    return await ticket_service.list(
        customer_id=customer_id,
        status=status,
        category=category,
        limit=limit,
        skip=skip,
    )
