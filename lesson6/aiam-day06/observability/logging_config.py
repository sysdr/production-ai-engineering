"""Structured JSON logging for the Day 6 observability stack."""
from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

# Extra fields we promote from the LogRecord into the JSON payload.
_EXTRA_FIELDS = ("route", "status", "latency_ms", "request_id")


class JSONFormatter(logging.Formatter):
    """Render each log record as a single-line JSON document."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logger(name: str = "aiam.obs") -> logging.Logger:
    """Return a logger that emits structured JSON to stdout (idempotent)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
