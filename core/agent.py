"""Agent query engine: retrieve context and generate answers.

Answers user questions via RAG with LLM fallback. This module must not
serve HTTP, Streamlit widgets, write uploads, or build indices directly.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from core.ingest import get_index
from core.llm_setup import configure_llama_settings, get_gemini_llm
from core.observability import trace_span
from core.resilience import safe_execute
from core.schemas import QueryInput, QueryResult
from core.settings import get_settings

logger = logging.getLogger("inayat")

_DISCLAIMERS = (
    "does not contain",
    "no information",
    "don't have",
    "not mentioned",
    "not clear",
    "does not mention",
    "cannot find",
)

_APOLOGY = (
    "I'm sorry, I'm having trouble connecting to my services right now. "
    "Please try again in a moment."
)


def _augment_prompt(question: str, memory_context: str) -> str:
    if memory_context:
        return (
            "You are I.N.A.Y.A.T., an intelligent AI assistant.\n"
            f"Here is what you remember about this user:\n{memory_context}\n\n"
            f"User question: {question}"
        )
    return question


def query_detailed(inp: QueryInput) -> QueryResult:
    """Answer a user question via RAG with structured result metadata.

    Flow:
        1. PropertyGraphIndex query engine (user-scoped metadata filter).
        2. Direct Gemini completion on insufficient RAG.
        3. Static apology when Gemini is unavailable.

    Args:
        inp: Validated query input.

    Returns:
        ``QueryResult`` with route, timing, and source metadata.
    """
    user = inp.resolved_user()
    settings = get_settings()
    started = time.perf_counter()
    augmented = _augment_prompt(inp.question, inp.memory_context)
    used_memory = bool(inp.memory_context.strip())

    with trace_span("agent.query", user_id=user.value):
        configure_llama_settings(settings)
        index = get_index(user.value)

        if index is not None:

            def _rag_query() -> Optional[tuple[str, int]]:
                from llama_index.core.vector_stores import MetadataFilter, MetadataFilters

                filters = MetadataFilters(
                    filters=[MetadataFilter(key="user_id", value=user.value)]
                )
                engine = index.as_query_engine(
                    include_text=True,
                    similarity_top_k=settings.similarity_top_k,
                    filters=filters,
                )
                response = engine.query(augmented)
                res_str = str(response)
                source_nodes = getattr(response, "source_nodes", None) or []
                source_count = len(source_nodes)

                if not source_nodes or any(
                    phrase in res_str.lower() for phrase in _DISCLAIMERS
                ):
                    logger.info("RAG context insufficient — falling back to pure LLM.")
                    return None

                return res_str, source_count

            rag_out = safe_execute(_rag_query, fallback=None)
            if rag_out is not None:
                answer, source_count = rag_out
                return QueryResult(
                    answer=answer,
                    route="rag",
                    source_count=source_count,
                    used_memory=used_memory,
                    latency_ms=round((time.perf_counter() - started) * 1000, 2),
                )

        logger.warning("RAG unavailable — falling back to pure Gemini chat.")

        def _llm_fallback() -> str:
            llm = get_gemini_llm()
            resp = llm.complete(augmented)
            return str(resp)

        fallback_answer = safe_execute(_llm_fallback, fallback=None)
        if fallback_answer is not None:
            return QueryResult(
                answer=fallback_answer,
                route="llm",
                source_count=0,
                used_memory=used_memory,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
            )

        return QueryResult(
            answer=_APOLOGY,
            route="apology",
            source_count=0,
            used_memory=used_memory,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
        )


def query(
    question: str,
    user_id: str = "default",
    memory_context: str = "",
) -> str:
    """Backwards-compatible string answer wrapper around ``query_detailed``.

    Args:
        question: User natural-language question.
        user_id: Profile identifier.
        memory_context: Pre-formatted memory bullets.

    Returns:
        Answer text only.
    """
    result = query_detailed(
        QueryInput.from_raw(question, user_id=user_id, memory_context=memory_context)
    )
    return result.answer


# Backwards-compatible re-exports (prefer ``core.ingest`` for new code).
from core.ingest import build_index, get_index  # noqa: E402,F401
