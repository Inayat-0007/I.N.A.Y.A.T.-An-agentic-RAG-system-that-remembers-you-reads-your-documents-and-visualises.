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
from core.observability import log_query_event, service_breaker_status, trace_span
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

_mmr_fallback_logged = False


def _build_query_engine(index, settings, filters):
    """Create a LlamaIndex query engine (optional MMR when enabled)."""
    global _mmr_fallback_logged

    base_kwargs = {
        "include_text": True,
        "similarity_top_k": settings.similarity_top_k,
        "filters": filters,
    }
    if not settings.mmr_enabled:
        return index.as_query_engine(**base_kwargs)

    try:
        return index.as_query_engine(
            vector_store_query_mode="mmr",
            mmr_threshold=settings.mmr_lambda,
            **base_kwargs,
        )
    except TypeError as exc:
        if not _mmr_fallback_logged:
            logger.warning(
                "MMR query mode not supported by installed LlamaIndex (%s); "
                "falling back to similarity_top_k=%s.",
                exc,
                settings.similarity_top_k,
            )
            _mmr_fallback_logged = True
        return index.as_query_engine(**base_kwargs)


def _augment_prompt(question: str, memory_context: str) -> str:
    if memory_context:
        return (
            "You are I.N.A.Y.A.T., an intelligent AI assistant.\n"
            f"Here is what you remember about this user:\n{memory_context}\n\n"
            f"User question: {question}"
        )
    return question


def _finalize_result(
    result: QueryResult,
    user_id: str,
    *,
    rag_ms: float | None = None,
    llm_ms: float | None = None,
) -> QueryResult:
    mem0_ok, neo4j_ok = service_breaker_status()
    log_query_event(
        user_id=user_id,
        route=result.route,
        latency_ms=result.latency_ms,
        source_count=result.source_count,
        mem0_ok=mem0_ok,
        neo4j_ok=neo4j_ok,
        rag_ms=rag_ms,
        llm_ms=llm_ms,
    )
    return result


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
    rag_ms: float | None = None
    llm_ms: float | None = None

    with trace_span("agent.query", user_id=user.value):
        configure_llama_settings(settings)
        index = get_index(user.value)

        if index is not None:

            def _rag_query() -> Optional[tuple[str, int]]:
                from llama_index.core.vector_stores import MetadataFilter, MetadataFilters

                filters = MetadataFilters(
                    filters=[MetadataFilter(key="user_id", value=user.value)]
                )
                engine = _build_query_engine(index, settings, filters)
                response = engine.query(augmented)
                res_str = str(response)
                source_nodes = getattr(response, "source_nodes", None) or []
                source_count = len(source_nodes)

                if not source_nodes:
                    logger.info("RAG context insufficient — falling back to pure LLM.")
                    return None
                if any(phrase in res_str.lower() for phrase in _DISCLAIMERS) and source_count == 0:
                    logger.info("RAG disclaimer with zero sources — falling back to pure LLM.")
                    return None

                return res_str, source_count

            rag_started = time.perf_counter()
            rag_out = safe_execute(_rag_query, fallback=None)
            rag_ms = round((time.perf_counter() - rag_started) * 1000, 2)
            if rag_out is not None:
                answer, source_count = rag_out
                return _finalize_result(
                    QueryResult(
                        answer=answer,
                        route="rag",
                        source_count=source_count,
                        used_memory=used_memory,
                        latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    ),
                    user.value,
                    rag_ms=rag_ms,
                )

        logger.warning("RAG unavailable — falling back to pure Gemini chat.")

        def _llm_fallback() -> str:
            llm = get_gemini_llm()
            resp = llm.complete(augmented)
            return str(resp)

        llm_started = time.perf_counter()
        fallback_answer = safe_execute(_llm_fallback, fallback=None)
        llm_ms = round((time.perf_counter() - llm_started) * 1000, 2)
        if fallback_answer is not None:
            return _finalize_result(
                QueryResult(
                    answer=fallback_answer,
                    route="llm",
                    source_count=0,
                    used_memory=used_memory,
                    latency_ms=round((time.perf_counter() - started) * 1000, 2),
                ),
                user.value,
                rag_ms=rag_ms,
                llm_ms=llm_ms,
            )

        return _finalize_result(
            QueryResult(
                answer=_APOLOGY,
                route="apology",
                source_count=0,
                used_memory=used_memory,
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
            ),
            user.value,
            rag_ms=rag_ms,
            llm_ms=llm_ms,
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
