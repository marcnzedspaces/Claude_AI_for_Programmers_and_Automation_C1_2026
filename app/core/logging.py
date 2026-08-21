import json
import logging
from typing import Any


LOGGER_NAME = "supportops"
logger = logging.getLogger(LOGGER_NAME)


def configure_logging(level: str) -> None:
    level_value = getattr(
        logging,
        level.upper(),
        logging.INFO,
    )

    logger.setLevel(level_value)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(message)s")
        )
        logger.addHandler(handler)

    logger.propagate = False


def log_event(
    event: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    payload = {
        "event": event,
        **fields,
    }

    logger.log(
        level,
        json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
            sort_keys=True,
        ),
    )
