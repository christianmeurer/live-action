from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from typing import Any


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(message)s")


def log_event(logger: logging.Logger, event: str, payload: dict[str, Any]) -> None:
    record: dict[str, Any] = {
        "ts": datetime.now(tz=UTC).isoformat(),
        "event": event,
        "payload": _normalize(payload),
    }
    logger.info(json.dumps(record, ensure_ascii=False))


def _normalize(value: Any) -> Any:
    if is_dataclass(value):
        return {k: _normalize(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    return value

