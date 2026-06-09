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

_DOC_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "documents")

# Dictionary cache for user-specific indices
_indices: dict = {}


# ---------------------------------------------------------------------------
# Index lifecycle
# ---------------------------------------------------------------------------

def _has_documents(user_id: str = "default") -> bool:
    """Return True when the user's documents directory contains at least one file."""
    user_dir = os.path.join(_DOC_ROOT, user_id)
    if not os.path.isdir(user_dir):
        return False
    files = [f for f in os.listdir(user_dir) if not f.startswith(".")]
    return len(files) > 0


def build_index(user_id: str = "default") -> Optional[PropertyGraphIndex]:
    """Build a new PropertyGraphIndex from the user's documents folder.

    Side effects:
        Calls ``configure_llama_settings()`` to ensure the global LLM and
        embedding models are set before indexing.

    Returns:
        The constructed index, or ``None`` on failure.
    """
    configure_llama_settings()
    graph_store = get_neo4j_property_graph_store()
    if graph_store is None:
        logger.warning("Neo4j graph store unavailable — cannot build index.")
        return None

    user_dir = os.path.join(_DOC_ROOT, user_id)
    os.makedirs(user_dir, exist_ok=True)

    if not _has_documents(user_id):
        logger.info("No documents in %s — loading existing graph index.", user_dir)
        try:
            _index = PropertyGraphIndex.from_existing(
                property_graph_store=graph_store,
            )
            _indices[user_id] = _index
            return _index
        except Exception as exc:
            logger.error("Failed to load existing index: %s", exc)
            return None

    try:
        reader = SimpleDirectoryReader(user_dir)
        docs = reader.load_data()
        
        # Attach user metadata for graph isolation
        for doc in docs:
            doc.metadata["user_id"] = user_id
            
        logger.info("Loaded %d document chunks for user %s from %s", len(docs), user_id, user_dir)

        _index = PropertyGraphIndex.from_documents(
            docs,
            property_graph_store=graph_store,
            show_progress=True,
        )
        logger.info("PropertyGraphIndex built successfully for user %s.", user_id)
        _indices[user_id] = _index
        return _index
    except Exception as exc:
        logger.error("Index build failed: %s", exc, exc_info=True)
        return None


def get_index(user_id: str = "default") -> Optional[PropertyGraphIndex]:
    """Return the cached index for the user, building it on first call.

    Returns:
        The ``PropertyGraphIndex``, or ``None`` when unavailable.
    """
    if user_id not in _indices or _indices[user_id] is None:
        _indices[user_id] = build_index(user_id)
    return _indices[user_id]


# ---------------------------------------------------------------------------
# Query interface
# ---------------------------------------------------------------------------

def query(
    question: str,
    user_id: str = "default",
    memory_context: str = "",
) -> str:
    """Answer a user question via RAG, with graceful fallback.

    Flow:
        1. Try the PropertyGraphIndex query engine (RAG + knowledge graph) filtered by user_id.
        2. If that fails, fall back to direct Gemini LLM chat.
        3. If *that* also fails, return an apologetic string.

    Args:
        question: The user's natural-language question.
        user_id: The active user profile name.
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
    index = get_index(user_id)
    if index is not None:
        def _rag_query() -> Optional[str]:
            from llama_index.core.vector_stores import MetadataFilters, MetadataFilter
            
            # Restrict vector retrieval to documents belonging to this user
            filters = MetadataFilters(
                filters=[MetadataFilter(key="user_id", value=user_id)]
            )
            
            engine = index.as_query_engine(
                include_text=True,
                similarity_top_k=5,
                filters=filters,
            )
            response = engine.query(augmented)
            res_str = str(response)
            disclaimers = [
                "does not contain",
                "no information",
                "don't have",
                "not mentioned",
                "not clear",
                "does not mention",
                "cannot find"
            ]
            if not getattr(response, "source_nodes", None) or any(d in res_str.lower() for d in disclaimers):
                logger.info("RAG context insufficient — falling back to pure LLM.")
                return None
            return res_str

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
