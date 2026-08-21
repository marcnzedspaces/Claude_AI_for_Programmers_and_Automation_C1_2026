from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import get_settings
from app.core.errors import (
    register_exception_handlers,
    request_id_middleware,
)
from app.core.logging import (
    configure_logging,
    log_event,
)
from app.database import (
    close_database,
    connect_to_database,
    get_database,
)
from app.repositories.ticket_repository import TicketRepository
from app.repositories.usage_repository import UsageRepository


settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_database()

    database = get_database()

    await UsageRepository(database).ensure_indexes()
    await TicketRepository(database).ensure_indexes()

    log_event(
        "application_ready",
        environment=settings.app_env,
        faq_cache_enabled=settings.faq_cache_enabled,
    )

    try:
        yield
    finally:
        await close_database()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.middleware("http")(request_id_middleware)
register_exception_handlers(app)
app.include_router(api_router)
