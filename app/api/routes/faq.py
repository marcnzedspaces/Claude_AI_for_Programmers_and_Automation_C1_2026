from fastapi import APIRouter, Request

from app.database import get_database
from app.repositories.faq_repository import FAQRepository
from app.repositories.usage_repository import UsageRepository
from app.schemas.faq import FAQAskRequest, FAQAskResponse
from app.schemas.usage import AIOperation, AIUsage
from app.services.claude_service import ClaudeService
from app.services.faq_service import FAQService
from app.services.usage_service import UsageService


router = APIRouter(
    prefix="/faq",
    tags=["faq"],
)


@router.post(
    "/ask",
    response_model=FAQAskResponse,
)
async def ask_faq(
    request: FAQAskRequest,
    http_request: Request,
) -> FAQAskResponse:
    database = get_database()
    claude_service = ClaudeService()
    usage_service = UsageService(
        UsageRepository(database)
    )

    service = FAQService(
        claude_service=claude_service,
        faq_repository=FAQRepository(database),
    )

    try:
        result = await service.ask(request.question)
    finally:
        await claude_service.close()

    usage = None

    if result.model is not None:
        usage = AIUsage(
            model=result.model,
            input_tokens=result.input_tokens or 0,
            output_tokens=result.output_tokens or 0,
            latency_ms=result.latency_ms or 0,
        )

        await usage_service.safe_record(
            request_id=http_request.state.request_id,
            operation=AIOperation.FAQ_ANSWER,
            usage=usage,
        )

    return FAQAskResponse(
        answer=result.answer,
        sources=result.sources,
        requires_human_review=result.requires_human_review,
        usage=usage,
    )
