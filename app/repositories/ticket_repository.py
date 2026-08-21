from typing import Any

from pymongo import ASCENDING, DESCENDING

from app.schemas.common import TicketCategory, TicketStatus
from app.schemas.ticket import TicketResponse


TICKET_PROJECTION = {
    "_id": 0,
}


class TicketRepository:
    def __init__(self, database: Any) -> None:
        self.collection = database.tickets

    async def ensure_indexes(self) -> None:
        await self.collection.create_index(
            "ticket_id",
            unique=True,
        )
        await self.collection.create_index(
            [("customer_id", ASCENDING), ("created_at", DESCENDING)],
        )
        await self.collection.create_index(
            [("status", ASCENDING), ("created_at", DESCENDING)],
        )
        await self.collection.create_index(
            [("analysis.category", ASCENDING), ("created_at", DESCENDING)],
        )

    async def insert(
        self,
        ticket: TicketResponse,
    ) -> TicketResponse:
        document = ticket.model_dump(mode="python")
        await self.collection.insert_one(document)
        return ticket

    async def replace(
        self,
        ticket: TicketResponse,
    ) -> TicketResponse:
        document = ticket.model_dump(mode="python")

        result = await self.collection.replace_one(
            {
                "ticket_id": ticket.ticket_id,
            },
            document,
        )

        if result.matched_count != 1:
            raise RuntimeError(
                f"Ticket {ticket.ticket_id} no longer exists."
            )

        return ticket

    async def get_by_id(
        self,
        ticket_id: str,
    ) -> TicketResponse | None:
        document = await self.collection.find_one(
            {
                "ticket_id": ticket_id,
            },
            TICKET_PROJECTION,
        )

        if document is None:
            return None

        return TicketResponse.model_validate(document)

    async def list(
        self,
        *,
        customer_id: str | None = None,
        status: TicketStatus | None = None,
        category: TicketCategory | None = None,
        limit: int = 20,
        skip: int = 0,
    ) -> tuple[list[TicketResponse], int]:
        query: dict[str, object] = {}

        if customer_id:
            query["customer_id"] = customer_id

        if status is not None:
            query["status"] = status.value

        if category is not None:
            query["analysis.category"] = category.value

        total = await self.collection.count_documents(query)

        cursor = (
            self.collection.find(
                query,
                TICKET_PROJECTION,
            )
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )

        items: list[TicketResponse] = []

        async for document in cursor:
            items.append(
                TicketResponse.model_validate(document)
            )

        return items, total
