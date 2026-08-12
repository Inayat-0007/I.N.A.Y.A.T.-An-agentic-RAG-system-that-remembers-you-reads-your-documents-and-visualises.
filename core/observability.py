"""Structured logging and request correlation.

Correlates logs and timings only. This module must not contain business logic.
"""

from __future__ import annotations

import contextvars
import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "inayat_request_id", default=""
)

logger = logging.getLogger("inayat")


def get_request_id() -> str:
    """Return the current request id, creating one if unset."""
    current = _request_id.get()
    if current:
        return current
    new_id = str(uuid.uuid4())
    _request_id.set(new_id)
    return new_id


def set_request_id(request_id: str) -> None:
    """Bind a request id for the current execution context."""
    _request_id.set(request_id)


@contextmanager
def trace_span(name: str, **attrs: Any) -> Iterator[dict[str, Any]]:
    """Log span start/end with latency and correlation id.

    Args:
        name: Span name (e.g. ``agent.query``).
        **attrs: Additional structured fields (user_id, route, etc.).

    Yields:
        Mutable span dict updated with ``latency_ms`` on exit.
    """
    span: dict[str, Any] = {
        "span": name,
        "request_id": get_request_id(),
        **attrs,
    }
    started = time.perf_counter()
    logger.info("span.start %s", span)
    try:
        yield span
    finally:
        span["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        logger.info("span.end %s", span)
