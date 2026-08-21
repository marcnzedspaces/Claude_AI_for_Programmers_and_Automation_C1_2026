from typing import Any

from app.config import get_settings
from app.core.cache import faq_search_cache
from app.core.logging import log_event
from app.schemas.faq import FAQSource


FAQ_SOURCE_PROJECTION = {
    "_id": 0,
    "faq_id": 1,
    "category": 1,
    "question": 1,
    "answer": 1,
}


class FAQRepository:
    def __init__(self, database: Any) -> None:
        self.collection = database.faqs
        self.settings = get_settings()

        faq_search_cache.configure(
            ttl_seconds=self.settings.faq_cache_ttl_seconds,
            max_entries=self.settings.faq_cache_max_entries,
        )

    async def get_by_ids(
        self,
        faq_ids: list[str],
        *,
        limit: int = 3,
    ) -> list[FAQSource]:
        requested_ids = list(dict.fromkeys(faq_ids))[:limit]

        if not requested_ids:
            return []

        cursor = self.collection.find(
            {
                "faq_id": {"$in": requested_ids},
                "active": True,
            },
            FAQ_SOURCE_PROJECTION,
        )

        found: dict[str, FAQSource] = {}

        async for document in cursor:
            faq = FAQSource.model_validate(document)
            found[faq.faq_id] = faq

        return [
            found[faq_id]
            for faq_id in requested_ids
            if faq_id in found
        ]

    async def search(
        self,
        query: str,
        *,
        limit: int = 3,
    ) -> list[FAQSource]:
        search_query = query.strip()

        if not search_query:
            return []

        safe_limit = max(1, min(limit, 3))

        if self.settings.faq_cache_enabled:
            cached = faq_search_cache.get(
                search_query,
                limit=safe_limit,
            )
            if cached is not None:
                log_event(
                    "faq_cache_hit",
                    limit=safe_limit,
                    result_count=len(cached),
                )
                return cached
            log_event(
                "faq_cache_miss",
                limit=safe_limit,
            )

        pipeline = [
            {
                "$match": {
                    "active": True,
                    "$text": {
                        "$search": search_query,
                    },
                }
            },
            {
                "$sort": {
                    "score": {
                        "$meta": "textScore",
                    }
                }
            },
            {
                "$limit": safe_limit,
            },
            {
                "$project": FAQ_SOURCE_PROJECTION,
            },
        ]

        cursor = await self.collection.aggregate(pipeline)

        results: list[FAQSource] = []

        async for document in cursor:
            results.append(
                FAQSource.model_validate(document)
            )

        if self.settings.faq_cache_enabled:
            faq_search_cache.set(
                search_query,
                limit=safe_limit,
                items=results,
            )

        return results
