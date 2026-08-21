from fastapi import APIRouter, Query

from app.database import get_database
from app.repositories.usage_repository import UsageRepository
from app.schemas.usage import (
    AIOperation,
    UsageResponse,
)
from app.services.usage_service import UsageService


router = APIRouter(
    prefix="/usage",
    tags=["usage"],
)


@router.get(
    "",
    response_model=UsageResponse,
)
async def get_usage(
    operation: AIOperation | None = Query(
        default=None,
    ),
    model: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    request_id: str | None = Query(
        default=None,
        min_length=3,
        max_length=100,
    ),
    ticket_id: str | None = Query(
        default=None,
        min_length=3,
        max_length=50,
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
) -> UsageResponse:
    service = UsageService(
        UsageRepository(get_database())
    )

    return await service.query(
        operation=operation,
        model=model,
        request_id=request_id,
        ticket_id=ticket_id,
        limit=limit,
        skip=skip,
    )
