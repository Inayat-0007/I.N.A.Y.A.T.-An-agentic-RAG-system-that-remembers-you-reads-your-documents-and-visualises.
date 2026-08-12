"""Shared typed data contracts for the agent pipeline."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from core.identity import UserId


class QueryInput(BaseModel):
    """Validated input for a single agent query."""

    question: str = Field(min_length=1)
    user_id: str
    memory_context: str = ""

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question cannot be blank.")
        return stripped

    @classmethod
    def from_raw(
        cls, question: str, user_id: str = "default", memory_context: str = ""
    ) -> "QueryInput":
        """Build from primitive strings (validates user_id via ``resolved_user``)."""
        return cls(question=question, user_id=user_id, memory_context=memory_context)

    def resolved_user(self) -> UserId:
        """Return validated ``UserId`` (raises ``InvalidUserId``)."""
        return UserId.parse(self.user_id)


class QueryResult(BaseModel):
    """Structured agent response for APIs and observability."""

    answer: str
    route: Literal["rag", "llm", "apology"]
    source_count: int = 0
    used_memory: bool = False
    latency_ms: float = 0.0
