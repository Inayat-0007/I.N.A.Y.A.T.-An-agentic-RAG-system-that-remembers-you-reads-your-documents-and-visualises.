"""Structured logging and request correlation.

Correlates logs and timings only. This module must not contain business logic.
"""

from __future__ import annotations

import contextvars
import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator, Literal

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "inayat_request_id", default=""
)

logger = logging.getLogger("inayat")

RouteName = Literal["rag", "llm", "apology"]


def new_request_id() -> str:
    """Return a new correlation id (UUID4 string)."""
    return str(uuid.uuid4())


def get_request_id() -> str:
    """Return the current request id, creating one if unset."""
    current = _request_id.get()
    if current:
        return current
    new_id = new_request_id()
    _request_id.set(new_id)
    return new_id


def set_request_id(request_id: str) -> None:
    """Bind a request id for the current execution context."""
    _request_id.set(request_id)


def service_breaker_status() -> tuple[bool, bool]:
    """Return (mem0_ok, neo4j_ok) from global service circuit breakers."""
    import core.graph_store as gs
    import core.memory as mem

    return mem._cb.allow_request(), gs._cb.allow_request()


def log_query_event(
    *,
    user_id: str,
    route: RouteName,
    latency_ms: float,
    source_count: int,
    mem0_ok: bool,
    neo4j_ok: bool,
    rag_ms: float | None = None,
    llm_ms: float | None = None,
) -> None:
    """Emit a structured query line (no prompts or secrets)."""
    parts = [
        "event=query",
        f"request_id={get_request_id()}",
        f"user_id={user_id}",
        f"route={route}",
        f"latency_ms={latency_ms}",
        f"source_count={source_count}",
        f"mem0_ok={str(mem0_ok).lower()}",
        f"neo4j_ok={str(neo4j_ok).lower()}",
    ]
    if rag_ms is not None:
        parts.append(f"rag_ms={rag_ms}")
    if llm_ms is not None:
        parts.append(f"llm_ms={llm_ms}")
    logger.info(" ".join(parts))


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
