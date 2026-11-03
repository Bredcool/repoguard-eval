"""Structured logging configuration."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from repoguard_eval.config import get_settings


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert a log record into a JSON string."""

        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(
    level: str | None = None,
    json_format: bool = True,
) -> None:
    """Configure the root logger."""

    settings = get_settings()
    log_level = (level or settings.log_level).upper()

    numeric_level = getattr(logging, log_level, None)

    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    handler = logging.StreamHandler()

    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
        )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """Return a named application logger."""

    return logging.getLogger(name)