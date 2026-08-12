"""Resilience utilities: retry, circuit breaker, and safe execution.

Every external call (Gemini, Mem0, Neo4j) flows through these wrappers
so that a single service outage never crashes the Streamlit app.
"""

import time
import threading
import logging
import functools
from typing import Callable, TypeVar, Any, Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger("inayat")
T = TypeVar("T")


# ---------------------------------------------------------------------------
# Circuit Breaker
# ---------------------------------------------------------------------------


class CircuitBreaker:
    """Lightweight circuit breaker that prevents hammering a dead service.

    States:
        CLOSED   – requests pass through normally.
        OPEN     – all requests are short-circuited immediately.
        HALF_OPEN – one probe request is allowed; success → CLOSED, fail → OPEN.
    """

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        *,
        service: str = "unknown",
    ) -> None:
        """Initialise the breaker.

        Args:
            failure_threshold: Consecutive failures before opening the circuit.
            recovery_timeout: Seconds to wait in OPEN state before probing.
            service: Service name for transition logs (Mem0, Neo4j, …).
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.service = service
        self._failure_count: int = 0
        self._state: str = self.CLOSED
        self._last_failure_time: float = 0.0
        self.forced_open: bool = False
        self._lock = threading.Lock()
        self._half_open_probing: bool = False

    def _transition(self, new_state: str) -> None:
        """Set state and log when it actually changes (caller holds lock)."""
        if new_state == self._state:
            return
        logger.info(
            "breaker_state=%s service=%s previous=%s",
            new_state,
            self.service,
            self._state,
        )
        self._state = new_state

    @property
    def state(self) -> str:
        """Return current state, auto-transitioning OPEN → HALF_OPEN if timeout elapsed."""
        with self._lock:
            if getattr(self, "forced_open", False):
                return self.OPEN
            if self._state == self.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._transition(self.HALF_OPEN)
            return self._state

    def record_success(self) -> None:
        """Reset the breaker on a successful call."""
        with self._lock:
            self._failure_count = 0
            self._transition(self.CLOSED)
            self._half_open_probing = False

    def record_failure(self) -> None:
        """Increment failure count; open the circuit if threshold exceeded."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            self._half_open_probing = False
            if self._failure_count >= self.failure_threshold:
                self._transition(self.OPEN)
                logger.warning(
                    "Circuit breaker OPENED after %d consecutive failures. "
                    "breaker_state=OPEN service=%s",
                    self._failure_count,
                    self.service,
                )

    def allow_request(self) -> bool:
        """Return True when the request should proceed."""
        with self._lock:
            if getattr(self, "forced_open", False):
                return False
            if self._state == self.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    self._transition(self.HALF_OPEN)
                else:
                    return False
            if self._state == self.HALF_OPEN:
                if self._half_open_probing:
                    return False
                self._half_open_probing = True
                return True
            return True


# ---------------------------------------------------------------------------
# Retry decorator (tenacity-backed)
# ---------------------------------------------------------------------------


def resilient_call(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
) -> Callable:
    """Decorator that retries a function with exponential back-off.

    Args:
        max_attempts: Total number of attempts (including the first).
        min_wait: Minimum seconds between retries.
        max_wait: Maximum seconds between retries.

    Returns:
        Decorated function with automatic retry behaviour.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Safe execute (catch-all with fallback)
# ---------------------------------------------------------------------------


def safe_execute(
    func: Callable[..., T],
    fallback: T,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Run *func* and return its result; on ANY exception return *fallback*.

    Args:
        func: Callable to invoke.
        fallback: Value returned when func raises.
        *args: Positional args forwarded to func.
        **kwargs: Keyword args forwarded to func.

    Returns:
        The function's return value, or *fallback* on error.
    """
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        logger.error(
            "safe_execute caught error in '%s': %s",
            getattr(func, "__name__", "anonymous"),
            exc,
            exc_info=True,
        )
        return fallback


# ---------------------------------------------------------------------------
# Demo-gated circuit breaker controls (HOW_TO_FIX §0.3 rule 4)
# ---------------------------------------------------------------------------


class DemoModeRequired(PermissionError):
    """Raised when forced_open is requested without INAYAT_DEMO_MODE=true."""


def clear_stale_forced_breakers() -> None:
    """Clear ``forced_open`` on module breakers when demo mode is off.

    Prevents a prior demo session from leaving Mem0/Neo4j forced open after
    ``INAYAT_DEMO_MODE`` is disabled or on a fresh process start without demo.
    """
    try:
        from core.settings import get_settings

        if get_settings().demo_mode:
            return
    except Exception:
        return

    for mod_name in ("core.memory", "core.graph_store"):
        try:
            import importlib

            mod = importlib.import_module(mod_name)
            cb = getattr(mod, "_cb", None)
            if cb is not None and getattr(cb, "forced_open", False):
                cb.forced_open = False
                logger.info(
                    "breaker_state=CLOSED service=%s reason=demo_mode_off",
                    getattr(cb, "service", mod_name),
                )
        except Exception:
            pass


def set_breaker_forced_open(
    breaker: CircuitBreaker, forced: bool, *, service: str = ""
) -> None:
    """Set ``forced_open`` on a breaker when demo mode is enabled.

    Direct assignment to ``breaker.forced_open`` is discouraged; use this helper
    so the demo script and API share one env-gated code path.
    """
    if forced:
        try:
            from core.settings import get_settings

            if not get_settings().demo_mode:
                label = service or "circuit breaker"
                raise DemoModeRequired(
                    f"{label} demo toggles require INAYAT_DEMO_MODE=true."
                )
        except DemoModeRequired:
            raise
        except Exception:
            raise DemoModeRequired(
                f"{service or 'Circuit breaker'} demo toggles require "
                "INAYAT_DEMO_MODE=true and valid configuration."
            ) from None
    breaker.forced_open = forced
    logger.info(
        "breaker_state=%s service=%s reason=forced_open value=%s",
        breaker.OPEN if forced else breaker.state,
        service or breaker.service,
        forced,
    )

