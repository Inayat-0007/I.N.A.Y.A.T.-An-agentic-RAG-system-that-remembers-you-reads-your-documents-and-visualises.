"""Mem0 cloud memory integration.

Wraps the Mem0 ``MemoryClient`` to provide persistent, cross-session user
memory.  Every call is protected by ``safe_execute`` so a Mem0 outage
never crashes the app — the agent simply answers without personalisation.
"""

import os
import logging
from typing import List, Optional

from mem0 import MemoryClient

from core.resilience import safe_execute, resilient_call, CircuitBreaker

logger = logging.getLogger("inayat")

# Circuit breaker shared across all memory operations
_cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)


# ---------------------------------------------------------------------------
# Client factory (cached at module level)
# ---------------------------------------------------------------------------

_client: Optional[MemoryClient] = None


def _get_client() -> Optional[MemoryClient]:
    """Lazily initialise and return the Mem0 cloud client.

    Returns:
        A ``MemoryClient`` instance, or ``None`` when the API key is missing.
    """
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("MEM0_API_KEY")
    if not api_key:
        logger.warning("MEM0_API_KEY not set — memory features disabled.")
        return None

    try:
        _client = MemoryClient(api_key=api_key)
        logger.info("Mem0 cloud client initialised.")
        return _client
    except Exception as exc:
        logger.error("Failed to create Mem0 client: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_memory(user_id: str, text: str) -> bool:
    """Store a user fact / interaction in Mem0.

    Args:
        user_id: Unique user identifier (e.g. their display name).
        text: The raw text to memorise.

    Returns:
        ``True`` on success, ``False`` on any failure.
    """
    if not _cb.allow_request():
        logger.debug("Mem0 circuit breaker OPEN — skipping add.")
        return False

    client = _get_client()
    if client is None:
        return False

    def _add() -> bool:
        client.add(text, user_id=user_id)
        _cb.record_success()
        return True

    result = safe_execute(_add, fallback=False)
    if not result:
        _cb.record_failure()
    return result


def get_memories(user_id: str) -> List[str]:
    """Retrieve all consolidated memories for a user.

    Args:
        user_id: Unique user identifier.

    Returns:
        A list of memory strings (may be empty on error).
    """
    if not _cb.allow_request():
        return []

    client = _get_client()
    if client is None:
        return []

    def _get() -> List[str]:
        raw = client.get_all(filters={"user_id": user_id})
        _cb.record_success()
        memories_list = raw.get("results", []) if isinstance(raw, dict) else raw
        if not memories_list:
            return []
        # Mem0 returns a list of dicts with a "memory" key
        return [m["memory"] for m in memories_list if isinstance(m, dict) and "memory" in m]

    sentinel = object()
    result = safe_execute(_get, fallback=sentinel)
    if result is sentinel:
        _cb.record_failure()
        return []
    return result


def search_memories(user_id: str, query: str, limit: int = 5) -> List[str]:
    """Semantic search over a user's memory store.

    Args:
        user_id: Unique user identifier.
        query: Natural-language search query.
        limit: Max results to return.

    Returns:
        Matching memory strings.
    """
    if not _cb.allow_request():
        return []

    client = _get_client()
    if client is None:
        return []

    def _search() -> List[str]:
        raw = client.search(query, filters={"user_id": user_id}, limit=limit)
        _cb.record_success()
        memories_list = raw.get("results", []) if isinstance(raw, dict) else raw
        if not memories_list:
            return []
        return [m["memory"] for m in memories_list if isinstance(m, dict) and "memory" in m]

    sentinel = object()
    result = safe_execute(_search, fallback=sentinel)
    if result is sentinel:
        _cb.record_failure()
        return []
    return result


def clear_memories(user_id: str) -> bool:
    """Delete all memories for a user.

    Args:
        user_id: Unique user identifier.

    Returns:
        ``True`` on success.
    """
    client = _get_client()
    if client is None:
        return False

    def _clear() -> bool:
        client.delete_all(user_id=user_id)
        return True

    return safe_execute(_clear, fallback=False)


def ping_mem0() -> bool:
    """Quick connectivity check for the Mem0 API.

    Returns:
        ``True`` when the client initialises without error.
    """
    client = _get_client()
    return client is not None
