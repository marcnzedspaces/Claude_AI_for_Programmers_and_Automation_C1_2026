from time import perf_counter

from fastapi import APIRouter, Request

from app.database import get_database
from app.repositories.faq_repository import FAQRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.usage_repository import UsageRepository
from app.schemas.ai import (
    AnalyseRequest,
    AnalyseResponse,
    GenerateResponseRequest,
    GenerateResponseResponse,
    ResponseContextUsed,
)
from app.schemas.usage import AIOperation, AIUsage
from app.services.analysis_service import AnalysisService
from app.services.claude_service import ClaudeService
from app.services.generate_response_service import (
    GenerateResponseService,
)
from app.services.response_service import ResponseService
from app.services.usage_service import UsageService


router = APIRouter(tags=["ai"])


@router.post("/analyse", response_model=AnalyseResponse)
async def analyse_ticket(
    request: AnalyseRequest,
    http_request: Request,
) -> AnalyseResponse:
    database = get_database()
    claude_service = ClaudeService()
    analysis_service = AnalysisService(claude_service)
    usage_service = UsageService(
        UsageRepository(database)
    )

    started = perf_counter()

    try:
        result = await analysis_service.analyse(request.message)
    finally:
        await claude_service.close()

    latency_ms = int((perf_counter() - started) * 1000)

    usage = AIUsage(
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=latency_ms,
    )

    await usage_service.safe_record(
        request_id=http_request.state.request_id,
        operation=AIOperation.TICKET_ANALYSIS,
        usage=usage,
    )

    return AnalyseResponse(
        analysis=result.data,
        usage=usage,
    )


@router.post(
    "/generate-response",
    response_model=GenerateResponseResponse,
)
async def generate_response(
    request: GenerateResponseRequest,
    http_request: Request,
) -> GenerateResponseResponse:
    database = get_database()
    claude_service = ClaudeService()
    usage_service = UsageService(
        UsageRepository(database)
    )

    service = GenerateResponseService(
        response_service=ResponseService(claude_service),
        order_repository=OrderRepository(database),
        faq_repository=FAQRepository(database),
    )

    try:
        result = await service.generate(request)
    finally:
        await claude_service.close()

    usage = AIUsage(
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        latency_ms=result.latency_ms,
    )

    await usage_service.safe_record(
        request_id=http_request.state.request_id,
        operation=AIOperation.RESPONSE_GENERATION,
        usage=usage,
    )

    return GenerateResponseResponse(
        draft_response=result.draft_response,
        context_used=ResponseContextUsed(
            order_id=result.order_id_used,
            faq_ids=result.faq_ids_used,
        ),
        usage=usage,
    )
