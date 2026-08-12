"""Short-term conversational turn buffer (server-side, optional).

Holds recent chat turns in process memory. This module must not call Mem0
or any long-term memory backend.
"""

from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Deque, Dict, List, Literal, TypedDict

from core.identity import UserId

DEFAULT_MAX_TURNS = 20

_lock = Lock()
_buffers: Dict[str, Deque["TurnRecord"]] = {}


class TurnRecord(TypedDict):
    role: Literal["user", "assistant"]
    content: str


def append_turn(
    user_id: str,
    role: Literal["user", "assistant"],
    content: str,
    *,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> None:
    """Append a chat turn to the in-memory buffer for a user.

    Args:
        user_id: Profile identifier (validated).
        role: ``user`` or ``assistant``.
        content: Message text.
        max_turns: Maximum turns retained (each user/assistant pair counts as two).
    """
    uid = UserId.parse(user_id).value
    turn: TurnRecord = {"role": role, "content": content}
    with _lock:
        if uid not in _buffers:
            _buffers[uid] = deque(maxlen=max(2, max_turns * 2))
        _buffers[uid].append(turn)


def recent_turns(user_id: str, limit: int = DEFAULT_MAX_TURNS) -> List[TurnRecord]:
    """Return the most recent turns for a user (may be empty).

    Args:
        user_id: Profile identifier (validated).
        limit: Max number of turns to return.

    Returns:
        List of turn dicts with ``role`` and ``content``.
    """
    uid = UserId.parse(user_id).value
    with _lock:
        buffer = _buffers.get(uid)
        if not buffer:
            return []
        return list(buffer)[-limit:]


def clear_turns(user_id: str) -> None:
    """Remove all buffered turns for a user."""
    uid = UserId.parse(user_id).value
    with _lock:
        _buffers.pop(uid, None)
