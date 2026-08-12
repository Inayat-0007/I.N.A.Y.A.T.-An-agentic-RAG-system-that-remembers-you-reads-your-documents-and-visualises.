"""Backwards-compatibility surface (HOW_TO_FIX §0.3).

Preserves legacy call sites while the typed architecture evolves underneath.
"""

from __future__ import annotations

from core.agent import build_index, get_index, query, query_detailed
from core.identity import InvalidUserId, UserId

__all__ = [
    "InvalidUserId",
    "UserId",
    "build_index",
    "get_index",
    "mem0_user_id",
    "query",
    "query_detailed",
]


def mem0_user_id(raw: str) -> str:
    """Validate a Mem0 tenant id without renaming it.

    Only normalises leading/trailing whitespace via ``UserId.parse``.
    The returned string is passed to Mem0 unchanged otherwise.
    """
    return UserId.parse(raw).value
