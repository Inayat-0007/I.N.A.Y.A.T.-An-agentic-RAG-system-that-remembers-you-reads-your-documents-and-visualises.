"""LlamaIndex RAG agent with PropertyGraphIndex over Neo4j.

Builds (or reloads) the property-graph index from PDFs in ``data/documents/``,
connects it to Neo4j for entity storage, and exposes a ``query()`` function
that the Streamlit UI calls for every user message.

Graceful degradation:
  • If Neo4j or document loading fails → fallback to pure Gemini chat.
  • If Gemini itself is down → return an apologetic string.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from llama_index.core import (
    PropertyGraphIndex,
    SimpleDirectoryReader,
    Settings,
)

from core.llm_setup import configure_llama_settings, get_gemini_llm
from core.graph_store import get_neo4j_property_graph_store
from core.resilience import safe_execute

logger = logging.getLogger("inayat")

_DOC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "documents")

# Module-level cache — built once, reused across Streamlit reruns
_index: Optional[PropertyGraphIndex] = None


# ---------------------------------------------------------------------------
# Index lifecycle
# ---------------------------------------------------------------------------

def _has_documents() -> bool:
    """Return True when the documents directory contains at least one file."""
    if not os.path.isdir(_DOC_DIR):
        return False
    files = [f for f in os.listdir(_DOC_DIR) if not f.startswith(".")]
    return len(files) > 0


def build_index() -> Optional[PropertyGraphIndex]:
    """Build a new PropertyGraphIndex from the documents folder.

    Side effects:
        Calls ``configure_llama_settings()`` to ensure the global LLM and
        embedding models are set before indexing.

    Returns:
        The constructed index, or ``None`` on failure.
    """
    global _index

    configure_llama_settings()
    graph_store = get_neo4j_property_graph_store()
    if graph_store is None:
        logger.warning("Neo4j graph store unavailable — cannot build index.")
        return None

    if not _has_documents():
        logger.info("No documents in %s — loading existing graph index.", _DOC_DIR)
        try:
            _index = PropertyGraphIndex.from_existing(
                property_graph_store=graph_store,
            )
            return _index
        except Exception as exc:
            logger.error("Failed to load existing index: %s", exc)
            return None

    try:
        reader = SimpleDirectoryReader(_DOC_DIR)
        docs = reader.load_data()
        logger.info("Loaded %d document chunks from %s", len(docs), _DOC_DIR)

        _index = PropertyGraphIndex.from_documents(
            docs,
            property_graph_store=graph_store,
            show_progress=True,
        )
        logger.info("PropertyGraphIndex built successfully.")
        return _index
    except Exception as exc:
        logger.error("Index build failed: %s", exc, exc_info=True)
        return None


def get_index() -> Optional[PropertyGraphIndex]:
    """Return the cached index, building it on first call.

    Returns:
        The ``PropertyGraphIndex``, or ``None`` when unavailable.
    """
    global _index
    if _index is None:
        _index = build_index()
    return _index


# ---------------------------------------------------------------------------
# Query interface
# ---------------------------------------------------------------------------

def query(
    question: str,
    memory_context: str = "",
) -> str:
    """Answer a user question via RAG, with graceful fallback.

    Flow:
        1. Try the PropertyGraphIndex query engine (RAG + knowledge graph).
        2. If that fails, fall back to direct Gemini LLM chat.
        3. If *that* also fails, return an apologetic string.

    Args:
        question: The user's natural-language question.
        memory_context: Pre-formatted user memories to inject into the prompt.

    Returns:
        The agent's answer as a string.
    """
    # Build an augmented prompt when memory context is available
    if memory_context:
        augmented = (
            f"You are I.N.A.Y.A.T., an intelligent AI assistant.\n"
            f"Here is what you remember about this user:\n{memory_context}\n\n"
            f"User question: {question}"
        )
    else:
        augmented = question

    # ---- Attempt 1: RAG via PropertyGraphIndex ----
    index = get_index()
    if index is not None:
        def _rag_query() -> str:
            engine = index.as_query_engine(
                include_text=True,
                similarity_top_k=5,
            )
            response = engine.query(augmented)
            return str(response)

        rag_answer = safe_execute(_rag_query, fallback=None)
        if rag_answer is not None:
            return rag_answer

    logger.warning("RAG unavailable — falling back to pure Gemini chat.")

    # ---- Attempt 2: Direct Gemini LLM ----
    def _llm_fallback() -> str:
        llm = get_gemini_llm()
        resp = llm.complete(augmented)
        return str(resp)

    fallback_answer = safe_execute(
        _llm_fallback,
        fallback="I'm sorry, I'm having trouble connecting to my services right now. Please try again in a moment.",
    )
    return fallback_answer
