from typing import Any

from pymongo import ASCENDING, DESCENDING

from app.schemas.usage import (
    AIOperation,
    AIUsageLog,
)


USAGE_PROJECTION = {
    "_id": 0,
}


class UsageRepository:
    def __init__(self, database: Any) -> None:
        self.collection = database.ai_usage_logs

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            "usage_id",
            unique=True,
        )
        await self.collection.create_index(
            "request_id",
        )
        await self.collection.create_index(
            "ticket_id",
        )
        await self.collection.create_index(
            [
                ("operation", ASCENDING),
                ("created_at", DESCENDING),
            ],
        )
        await self.collection.create_index(
            [
                ("created_at", DESCENDING),
            ],
        )

    async def insert(
        self,
        usage: AIUsageLog,
    ) -> AIUsageLog:
        await self.collection.insert_one(
            usage.model_dump(mode="python")
        )
        return usage

    async def list(
        self,
        *,
        operation: AIOperation | None = None,
        model: str | None = None,
        request_id: str | None = None,
        ticket_id: str | None = None,
        limit: int = 20,
        skip: int = 0,
    ) -> tuple[list[AIUsageLog], int]:
        query = self._build_query(
            operation=operation,
            model=model,
            request_id=request_id,
            ticket_id=ticket_id,
        )

        total = await self.collection.count_documents(
            query
        )

        cursor = (
            self.collection.find(
                query,
                USAGE_PROJECTION,
            )
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )

        items: list[AIUsageLog] = []

        async for document in cursor:
            items.append(
                AIUsageLog.model_validate(document)
            )

        return items, total

    async def summarize(
        self,
        *,
        operation: AIOperation | None = None,
        model: str | None = None,
        request_id: str | None = None,
        ticket_id: str | None = None,
    ) -> dict[str, int | float]:
        query = self._build_query(
            operation=operation,
            model=model,
            request_id=request_id,
            ticket_id=ticket_id,
        )

        pipeline = [
            {
                "$match": query,
            },
            {
                "$group": {
                    "_id": None,
                    "total_calls": {
                        "$sum": 1,
                    },
                    "total_input_tokens": {
                        "$sum": "$input_tokens",
                    },
                    "total_output_tokens": {
                        "$sum": "$output_tokens",
                    },
                    "total_tokens": {
                        "$sum": "$total_tokens",
                    },
                    "estimated_cost_usd": {
                        "$sum": "$estimated_cost_usd",
                    },
                    "average_latency_ms": {
                        "$avg": "$latency_ms",
                    },
                }
            },
        ]

        cursor = await self.collection.aggregate(
            pipeline
        )

        async for document in cursor:
            return {
                "total_calls": int(
                    document.get(
                        "total_calls",
                        0,
                    )
                ),
                "total_input_tokens": int(
                    document.get(
                        "total_input_tokens",
                        0,
                    )
                ),
                "total_output_tokens": int(
                    document.get(
                        "total_output_tokens",
                        0,
                    )
                ),
                "total_tokens": int(
                    document.get(
                        "total_tokens",
                        0,
                    )
                ),
                "estimated_cost_usd": float(
                    document.get(
                        "estimated_cost_usd",
                        0.0,
                    )
                ),
                "average_latency_ms": float(
                    document.get(
                        "average_latency_ms",
                        0.0,
                    )
                ),
            }

        return {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "average_latency_ms": 0.0,
        }

    @staticmethod
    def _build_query(
        *,
        operation: AIOperation | None,
        model: str | None,
        request_id: str | None,
        ticket_id: str | None,
    ) -> dict[str, object]:
        query: dict[str, object] = {}

        if operation is not None:
            query["operation"] = operation.value

        if model:
            query["model"] = model

        if request_id:
            query["request_id"] = request_id

        if ticket_id:
            query["ticket_id"] = ticket_id

        return query
