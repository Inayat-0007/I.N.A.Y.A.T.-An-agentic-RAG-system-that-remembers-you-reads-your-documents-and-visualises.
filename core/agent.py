"""Agent query engine: retrieve context and generate answers.

Answers user questions via RAG with LLM fallback. This module must not
serve HTTP, Streamlit widgets, write uploads, or build indices directly.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from core.graph_store import retrieve_user_chunks
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

        def _chunk_rag() -> Optional[tuple[str, int]]:
            chunks = retrieve_user_chunks(
                user.value, inp.question, top_k=settings.similarity_top_k
            )
            if not chunks:
                logger.info("No user-scoped chunks — falling back to pure LLM.")
                return None
            excerpts = []
            for row in chunks:
                name = row.get("file_name") or "document"
                text = (row.get("text") or "").strip()
                if not text:
                    continue
                excerpts.append(f"[{name}]\n{text[:4000]}")
            if not excerpts:
                return None
            context = "\n\n".join(excerpts)
            prompt = (
                "You are I.N.A.Y.A.T. Answer using only the document excerpts "
                "below. Do not use facts from other user profiles or prior "
                "workspaces. If the excerpts are insufficient, say so briefly.\n\n"
                f"{context}\n\n"
                f"User question: {inp.question}"
            )
            llm = get_gemini_llm()
            return str(llm.complete(prompt)), len(excerpts)

        rag_started = time.perf_counter()
        rag_out = safe_execute(_chunk_rag, fallback=None)
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
            if used_memory:
                prompt = augmented
            else:
                prompt = (
                    "You are I.N.A.Y.A.T. This workspace has no indexed documents "
                    "and no memories for this profile. Answer the question generally. "
                    "Do not claim knowledge from other user profiles or leftover "
                    "sessions.\n\n"
                    f"User question: {inp.question}"
                )
            resp = llm.complete(prompt)
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
