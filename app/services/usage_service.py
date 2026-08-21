import logging
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from app.config import get_settings
from app.core.ids import new_usage_id
from app.core.logging import log_event
from app.repositories.usage_repository import UsageRepository
from app.schemas.usage import (
    AIOperation,
    AIUsage,
    AIUsageLog,
    UsageResponse,
    UsageSummary,
)


class UsageService:
    def __init__(
        self,
        repository: UsageRepository,
    ) -> None:
        self.repository = repository
        self.settings = get_settings()

    def estimate_cost_usd(
        self,
        usage: AIUsage,
    ) -> float:
        input_cost = (
            usage.input_tokens
            / 1_000_000
            * self.settings.claude_input_cost_per_million_usd
        )
        output_cost = (
            usage.output_tokens
            / 1_000_000
            * self.settings.claude_output_cost_per_million_usd
        )

        return round(
            input_cost + output_cost,
            8,
        )

    async def record(
        self,
        *,
        request_id: str,
        operation: AIOperation,
        usage: AIUsage,
        ticket_id: str | None = None,
    ) -> AIUsageLog:
        record = AIUsageLog(
            usage_id=new_usage_id(),
            request_id=request_id,
            ticket_id=ticket_id,
            operation=operation,
            model=usage.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=(
                usage.input_tokens
                + usage.output_tokens
            ),
            latency_ms=usage.latency_ms,
            estimated_cost_usd=(
                self.estimate_cost_usd(usage)
            ),
            created_at=datetime.now(timezone.utc),
        )

        inserted = await self.repository.insert(record)

        log_event(
            "ai_usage",
            request_id=request_id,
            ticket_id=ticket_id,
            operation=operation.value,
            model=usage.model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=usage.latency_ms,
            estimated_cost_usd=(
                inserted.estimated_cost_usd
            ),
        )

        return inserted

    async def safe_record(
        self,
        *,
        request_id: str,
        operation: AIOperation,
        usage: AIUsage,
        ticket_id: str | None = None,
    ) -> AIUsageLog | None:
        try:
            return await self.record(
                request_id=request_id,
                operation=operation,
                usage=usage,
                ticket_id=ticket_id,
            )
        except PyMongoError:
            log_event(
                "ai_usage_persist_failed",
                level=logging.WARNING,
                request_id=request_id,
                ticket_id=ticket_id,
                operation=operation.value,
            )
            return None

    async def query(
        self,
        *,
        operation: AIOperation | None = None,
        model: str | None = None,
        request_id: str | None = None,
        ticket_id: str | None = None,
        limit: int = 20,
        skip: int = 0,
    ) -> UsageResponse:
        items, total = await self.repository.list(
            operation=operation,
            model=model,
            request_id=request_id,
            ticket_id=ticket_id,
            limit=limit,
            skip=skip,
        )

        summary_data = await self.repository.summarize(
            operation=operation,
            model=model,
            request_id=request_id,
            ticket_id=ticket_id,
        )

        return UsageResponse(
            summary=UsageSummary(
                total_calls=int(
                    summary_data["total_calls"]
                ),
                total_input_tokens=int(
                    summary_data[
                        "total_input_tokens"
                    ]
                ),
                total_output_tokens=int(
                    summary_data[
                        "total_output_tokens"
                    ]
                ),
                total_tokens=int(
                    summary_data["total_tokens"]
                ),
                estimated_cost_usd=round(
                    float(
                        summary_data[
                            "estimated_cost_usd"
                        ]
                    ),
                    8,
                ),
                average_latency_ms=round(
                    float(
                        summary_data[
                            "average_latency_ms"
                        ]
                    ),
                    2,
                ),
            ),
            items=items,
            total=total,
            limit=limit,
            skip=skip,
        )
