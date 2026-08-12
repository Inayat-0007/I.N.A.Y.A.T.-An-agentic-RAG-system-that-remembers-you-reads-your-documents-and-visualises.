"""User identity parsing and sanitization.

Validates ``user_id`` strings only. This module must not persist files
or query databases.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_WIN_RESERVED = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
)

_USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class InvalidUserId(ValueError):
    """Raised when a user identifier fails validation."""


@dataclass(frozen=True, slots=True)
class UserId:
    """Validated, immutable user identifier."""

    value: str

    @classmethod
    def parse(cls, raw: str) -> "UserId":
        """Parse and sanitize a raw user id string.

        Args:
            raw: Display name / profile id from UI or API.

        Returns:
            A validated ``UserId``.

        Raises:
            InvalidUserId: When the value is empty, unsafe, or malformed.
        """
        if raw is None:
            raise InvalidUserId("user_id is required.")

        candidate = raw.strip()
        if not candidate:
            raise InvalidUserId("user_id cannot be empty.")
        if len(candidate) > 64:
            raise InvalidUserId("user_id must be at most 64 characters.")
        if candidate in (".", ".."):
            raise InvalidUserId("user_id cannot be '.' or '..'.")
        if any(sep in candidate for sep in ("/", "\\", "\x00")):
            raise InvalidUserId("user_id cannot contain path separators.")
        if not _USER_ID_PATTERN.match(candidate):
            raise InvalidUserId(
                "user_id must start with alphanumeric and contain only "
                "letters, digits, '.', '_', or '-'."
            )

        stem = candidate.split(".")[0].upper()
        if stem in _WIN_RESERVED:
            raise InvalidUserId(f"user_id '{candidate}' is a reserved name.")

        return cls(value=candidate)

    def __str__(self) -> str:
        return self.value
