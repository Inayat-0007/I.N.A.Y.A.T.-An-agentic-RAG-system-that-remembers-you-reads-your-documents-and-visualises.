"""Shared typed data contracts for the agent pipeline."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.identity import InvalidUserId, UserId


class QueryInput(BaseModel):
    """Validated input for a single agent query."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    question: str = Field(min_length=1)
    user_id: UserId
    memory_context: str = ""

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question cannot be blank.")
        return stripped

    @field_validator("user_id", mode="before")
    @classmethod
    def coerce_user_id(cls, value: object) -> UserId:
        if isinstance(value, UserId):
            return value
        if isinstance(value, str):
            return UserId.parse(value)
        raise InvalidUserId("user_id must be a string or UserId.")

    @classmethod
    def from_raw(
        cls, question: str, user_id: str = "default", memory_context: str = ""
    ) -> "QueryInput":
        """Build from primitive strings (validates ``user_id``)."""
        return cls(
            question=question,
            user_id=UserId.parse(user_id),
            memory_context=memory_context,
        )

    def resolved_user(self) -> UserId:
        """Return validated ``UserId``."""
        return self.user_id


class QueryResult(BaseModel):
    """Structured agent response for APIs and observability."""

    answer: str
    route: Literal["rag", "llm", "apology"]
    source_count: int = 0
    used_memory: bool = False
    latency_ms: float = 0.0
