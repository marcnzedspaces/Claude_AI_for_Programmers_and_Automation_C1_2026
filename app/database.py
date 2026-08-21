from typing import Any

from pymongo import AsyncMongoClient

from app.config import get_settings


_client: AsyncMongoClient | None = None
_database: Any = None


async def connect_to_database() -> None:
    # Create the shared MongoDB client and verify connectivity.
    global _client, _database

    if _client is not None:
        return

    settings = get_settings()
    client = AsyncMongoClient(
        settings.mongodb_uri.get_secret_value()
    )

    try:
        await client.admin.command("ping")
    except Exception:
        await client.close()
        raise

    _client = client
    _database = client[settings.mongodb_database]


async def ping_database() -> None:
    # Verify that the active client can reach MongoDB.
    if _client is None:
        raise RuntimeError("Database has not been connected.")

    await _client.admin.command("ping")


def get_database() -> Any:
    # Return the configured application database.
    if _database is None:
        raise RuntimeError("Database has not been connected.")

    return _database


async def close_database() -> None:
    # Close the shared MongoDB client during shutdown.
    global _client, _database

    if _client is not None:
        await _client.close()

    _client = None
    _database = None
