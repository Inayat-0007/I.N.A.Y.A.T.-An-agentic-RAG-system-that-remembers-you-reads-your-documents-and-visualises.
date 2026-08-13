"""Neo4j AuraDB driver and Cypher query wrapper.

Manages a singleton ``neo4j.Driver`` connection pool and exposes a
resilient ``run_cypher`` helper.  Also provides the
``get_neo4j_property_graph_store`` factory used by the LlamaIndex
``PropertyGraphIndex``.
"""

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from neo4j import Driver, GraphDatabase

from core.resilience import CircuitBreaker, resilient_call, safe_execute
from core.identity import UserId
from core.settings import InayatSettings, get_settings

logger = logging.getLogger("inayat")

_driver: Optional[Driver] = None
_driver_lock = threading.Lock()
_cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60, service="Neo4j")


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------


def _get_credentials(settings: Optional[InayatSettings] = None) -> tuple[str, str, str]:
    """Return (uri, username, password) from application settings.

    Raises:
        ValueError: When mandatory vars are missing.
    """
    cfg = settings or get_settings()
    if not cfg.neo4j_uri or not cfg.neo4j_password:
        raise ValueError("NEO4J_URI / NEO4J_PASSWORD missing from environment.")
    return cfg.neo4j_uri, cfg.neo4j_username, cfg.neo4j_password


def get_driver() -> Optional[Driver]:
    """Lazily create and return the global Neo4j driver.

    Returns:
        A ``Driver`` instance, or ``None`` when credentials are missing.
    """
    global _driver
    if _driver is not None:
        return _driver
    with _driver_lock:
        if _driver is not None:
            return _driver

        try:
            uri, user, pwd = _get_credentials()
            _driver = GraphDatabase.driver(uri, auth=(user, pwd))
            logger.info("Neo4j driver created for %s", uri)
            return _driver
        except Exception as exc:
            logger.error("Neo4j driver creation failed: %s", exc)
            return None


def close_driver() -> None:
    """Shut down the Neo4j connection pool cleanly."""
    global _driver
    with _driver_lock:
        if _driver:
            _driver.close()
            _driver = None
            logger.info("Neo4j driver closed.")


# ---------------------------------------------------------------------------
# Cypher query runner
# ---------------------------------------------------------------------------


def run_cypher(
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Execute a Cypher statement and return result records as dicts.

    Protected by circuit breaker + safe_execute.

    Args:
        query: Cypher query string.
        parameters: Optional bind parameters.

    Returns:
        A (possibly empty) list of record dicts.
    """
    if not _cb.allow_request():
        logger.debug("Neo4j circuit breaker OPEN — skipping query.")
        return []

    driver = get_driver()
    if not driver:
        return []

    def _run() -> List[Dict[str, Any]]:
        uri, user, pwd = _get_credentials()
        is_write = any(
            kw in query.upper()
            for kw in ["CREATE", "MERGE", "SET", "DELETE", "REMOVE", "DETACH"]
        )

        with driver.session(database=user) as session:
            if is_write:
                records = session.execute_write(
                    lambda tx: [dict(r) for r in tx.run(query, parameters or {})]
                )
            else:
                records = session.execute_read(
                    lambda tx: [dict(r) for r in tx.run(query, parameters or {})]
                )
        _cb.record_success()
        return records

    sentinel = object()
    out = safe_execute(_run, fallback=sentinel)
    if out is sentinel:
        _cb.record_failure()
        return []
    return out


# ---------------------------------------------------------------------------
# LlamaIndex integration
# ---------------------------------------------------------------------------


def get_neo4j_property_graph_store() -> Optional[Neo4jPropertyGraphStore]:
    """Create a ``Neo4jPropertyGraphStore`` for LlamaIndex.

    Returns:
        The graph store, or ``None`` on failure.
    """
    try:
        uri, user, pwd = _get_credentials()
        store = Neo4jPropertyGraphStore(
            username=user,
            password=pwd,
            url=uri,
            database=user,
        )
        logger.info("Neo4jPropertyGraphStore created.")
        return store
    except Exception as exc:
        logger.error("Failed to create Neo4jPropertyGraphStore: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@resilient_call(max_attempts=2, min_wait=1, max_wait=5)
def ping_neo4j() -> bool:
    """Verify connectivity to Neo4j AuraDB.

    Returns:
        ``True`` when a simple ``RETURN 1`` succeeds.

    Raises:
        Exception: On connection failure (retried by decorator).
    """
    driver = get_driver()
    if not driver:
        raise ConnectionError("No Neo4j driver available.")
    uri, user, pwd = _get_credentials()
    # Verify driver connectivity and database responsiveness
    driver.verify_connectivity()
    with driver.session(database=user) as session:
        session.run("RETURN 1").consume()
    logger.debug("Neo4j ping OK")
    return True


def _mock_visualization_graph(
    user_id: str = "default",
    *,
    reason: str = "no_documents",
) -> dict:
    """Empty vis payload when this profile has no chunks (or Neo4j is down).

    Architecture nodes are not mixed into the knowledge graph. The landing
    page owns the system diagram. ``reason`` is ``no_documents`` or ``offline``.
    """
    return {
        "nodes": [],
        "edges": [],
        "is_mock": True,
        "mock_reason": reason,
        "user_id": user_id,
    }


def delete_user_chunks(user_id: str) -> int:
    """Detach-delete Chunk nodes for one profile. Returns deleted count."""
    uid = UserId.parse(user_id).value
    rows = run_cypher(
        """
        MATCH (c:Chunk {user_id: $user_id})
        WITH c
        DETACH DELETE c
        RETURN count(*) AS n
        """,
        {"user_id": uid},
    )
    deleted = int(rows[0]["n"]) if rows else 0
    logger.info("Deleted %d Chunk node(s) for user %s", deleted, uid)
    return deleted


def retrieve_user_chunks(
    user_id: str,
    question: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Return this user's Chunk texts ranked by embedding similarity.

    PropertyGraphIndex vector search hits ``__Entity__`` nodes (LLM triplets).
    ImplicitPathExtractor ingest writes Chunk embeddings only, so chat must
    query Chunk nodes filtered by ``user_id`` — not the shared entity index.
    """
    uid = UserId.parse(user_id).value
    k = max(1, int(top_k))
    embedding: Optional[List[float]] = None
    try:
        from llama_index.core import Settings as LISettings

        from core.llm_setup import configure_llama_settings

        configure_llama_settings()
        embed_model = getattr(LISettings, "embed_model", None)
        if embed_model is not None:
            embedding = list(embed_model.get_text_embedding(question))
    except Exception as exc:
        logger.warning("Could not embed question for chunk retrieval: %s", exc)

    if embedding:
        rows = run_cypher(
            """
            MATCH (c:Chunk {user_id: $user_id})
            WHERE c.embedding IS NOT NULL
              AND c.text IS NOT NULL
              AND NOT c.text STARTS WITH '%PDF'
            WITH c, vector.similarity.cosine(c.embedding, $embedding) AS score
            ORDER BY score DESC
            LIMIT $k
            RETURN c.text AS text, c.file_name AS file_name, score
            """,
            {"user_id": uid, "embedding": embedding, "k": k},
        )
        if rows:
            return rows

    rows = run_cypher(
        """
        MATCH (c:Chunk {user_id: $user_id})
        WHERE c.text IS NOT NULL AND NOT c.text STARTS WITH '%PDF'
        RETURN c.text AS text, c.file_name AS file_name, 0.0 AS score
        LIMIT $k
        """,
        {"user_id": uid, "k": k},
    )
    return rows


def stamp_chunks_for_user(user_id: str, file_names: Sequence[str]) -> int:
    """Set ``user_id`` on Chunks whose file_path belongs to this profile."""
    uid = UserId.parse(user_id).value
    names = [Path(name).name for name in file_names if name]
    if not names:
        return 0
    rows = run_cypher(
        """
        MATCH (c:Chunk)
        WHERE c.file_name IN $files
          AND (
            c.user_id = $user_id
            OR c.file_path CONTAINS $needle_slash
            OR c.file_path CONTAINS $needle_win
          )
        SET c.user_id = $user_id
        RETURN count(c) AS n
        """,
        {
            "user_id": uid,
            "files": names,
            "needle_slash": f"documents/{uid}",
            "needle_win": f"documents\\{uid}",
        },
    )
    stamped = int(rows[0]["n"]) if rows else 0
    logger.info("Stamped user_id on %d Chunk node(s) for %s", stamped, uid)
    return stamped


_INTERNAL_LABEL_PREFIX = "__"
_PROP_SKIP = {
    "embedding",
    "_node_content",
    "_node_type",
    "id",
    "doc_id",
    "document_id",
    "ref_doc_id",
    "file_path",
    "file_size",
    "creation_date",
    "last_modified_date",
}


def _public_labels(labels: Optional[List[str]]) -> List[str]:
    """Drop LlamaIndex internal labels such as ``__Node__`` / ``__Entity__``."""
    raw = [str(item) for item in (labels or []) if item]
    public = [item for item in raw if not item.startswith(_INTERNAL_LABEL_PREFIX)]
    return public or ["Entity"]


def _vis_group(labels: Optional[List[str]]) -> str:
    group = _public_labels(labels)[0]
    lowered = group.lower()
    if lowered == "chunk":
        return "Chunk"
    if lowered == "entity":
        return "Entity"
    return group


def _text_snippet(text: Any, limit: int = 48) -> str:
    """First readable line of chunk text for graph labels (never PDF bytes)."""
    if not isinstance(text, str):
        return ""
    stripped = text.strip()
    if not stripped or stripped.startswith("%PDF") or stripped == "[PDF binary omitted]":
        return ""
    for line in stripped.splitlines():
        cleaned = " ".join(line.split())
        if len(cleaned) >= 4:
            return cleaned[:limit] + ("…" if len(cleaned) > limit else "")
    cleaned = " ".join(stripped.split())
    return cleaned[:limit] + ("…" if len(cleaned) > limit else "")


def _node_display_label(
    labels: Optional[List[str]],
    props: dict,
    name: Any,
    nid: str,
) -> str:
    """Human label from document text, not LlamaIndex architecture names."""
    group = _vis_group(labels)
    snippet = _text_snippet(props.get("text"), 48)
    if group == "Chunk" and snippet:
        return snippet
    if isinstance(name, str) and name.strip() and not name.startswith(_INTERNAL_LABEL_PREFIX):
        return name.strip()[:60]
    named = props.get("name")
    if isinstance(named, str) and named.strip() and not named.startswith(_INTERNAL_LABEL_PREFIX):
        return named.strip()[:60]
    file_name = props.get("file_name")
    if file_name:
        stem = Path(str(file_name)).stem.strip()
        if stem:
            return stem[:48]
    return group


def _node_allowed_for_user(labels: List[str], props: dict, user_id: str) -> bool:
    """Return True when a graph node may be shown for the given user.

    Chunks must match ``user_id``. Nodes with a different ``user_id`` property
    are always stripped. Entities without a user_id are decided at graph
    assembly time (every connected Chunk in the result set must belong to
    this user).
    """
    label_list = labels or ["Entity"]
    node_user = props.get("user_id")
    if node_user not in (None, user_id):
        return False
    if "Chunk" in label_list:
        return node_user == user_id
    return True


def _assemble_visualization(records: List[dict], user_id: str) -> dict:
    """Build vis payload from Cypher rows with strict user isolation."""

    def clean_props(props: Optional[dict]) -> dict:
        if not props:
            return {}
        cleaned = {}
        for key, value in props.items():
            if key in _PROP_SKIP:
                continue
            if key == "text":
                if not isinstance(value, str):
                    continue
                if value.lstrip().startswith("%PDF"):
                    cleaned[key] = "[PDF binary omitted]"
                    continue
                preview = "".join(
                    ch if ch.isprintable() or ch in "\n\t" else " "
                    for ch in value[:180]
                )
                cleaned[key] = preview + ("..." if len(value) > 180 else "")
                continue
            cleaned[key] = value
        return cleaned

    raw_nodes: dict = {}
    raw_edges: list = []
    neighbors: dict[str, set] = {}

    def _touch(nid: str) -> None:
        neighbors.setdefault(nid, set())

    for rec in records:
        s_id = rec.get("source_id")
        t_id = rec.get("target_id")
        if not s_id:
            continue
        s_props = clean_props(rec.get("source_props"))
        s_labels = rec.get("source_labels") or ["Entity"]
        raw_nodes[s_id] = {
            "labels": s_labels,
            "props": s_props,
            "name": rec.get("source_name"),
        }
        _touch(s_id)
        if t_id:
            t_props = clean_props(rec.get("target_props"))
            t_labels = rec.get("target_labels") or ["Entity"]
            raw_nodes[t_id] = {
                "labels": t_labels,
                "props": t_props,
                "name": rec.get("target_name"),
            }
            raw_edges.append(
                {
                    "from": s_id,
                    "to": t_id,
                    "label": rec.get("rel_type") or "RELATED",
                    "properties": clean_props(rec.get("rel_props")),
                }
            )
            _touch(t_id)
            neighbors[s_id].add(t_id)
            neighbors[t_id].add(s_id)

    chunk_owner: dict = {}
    for nid, node in raw_nodes.items():
        if "Chunk" in (node["labels"] or []):
            chunk_owner[nid] = node["props"].get("user_id")

    allowed: set = set()
    for nid, node in raw_nodes.items():
        if not _node_allowed_for_user(node["labels"], node["props"], user_id):
            continue
        labels = node["labels"] or ["Entity"]
        if "Chunk" not in labels:
            connected_chunks = [
                cid for cid in neighbors.get(nid, set()) if cid in chunk_owner
            ]
            if connected_chunks and any(
                chunk_owner[cid] != user_id for cid in connected_chunks
            ):
                continue
        allowed.add(nid)

    user_chunks = [
        nid
        for nid in allowed
        if "Chunk" in (raw_nodes[nid]["labels"] or [])
        and raw_nodes[nid]["props"].get("user_id") == user_id
    ]
    if not user_chunks:
        return _mock_visualization_graph(user_id, reason="no_documents")

    nodes: dict = {}
    edges: list = []
    for nid in allowed:
        node = raw_nodes[nid]
        labels = node["labels"] or ["Entity"]
        group = _vis_group(labels)
        props = node["props"]
        display = _node_display_label(labels, props, node["name"], nid)
        hover = _text_snippet(props.get("text"), 140) or display
        nodes[nid] = {
            "id": nid,
            "label": display,
            "group": group,
            "properties": props,
            "title": f"{group}: {hover}",
        }

    edge_index = 0
    for edge in raw_edges:
        if edge["from"] in allowed and edge["to"] in allowed:
            edge_index += 1
            edges.append({**edge, "id": edge.get("id") or f"e{edge_index}"})

    if not nodes:
        return _mock_visualization_graph(user_id, reason="no_documents")
    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "is_mock": False,
        "mock_reason": None,
    }


def _neo4j_reachable() -> bool:
    """Return True when the driver can run a trivial query."""
    if not _cb.allow_request() or get_driver() is None:
        return False
    try:
        ping_neo4j()
        return True
    except Exception:
        return False


def get_visualization_data(user_id: str = "default") -> dict:
    """Retrieve user-scoped nodes/edges; empty canvas when empty or offline."""
    uid = UserId.parse(user_id).value
    if not _cb.allow_request() or get_driver() is None:
        logger.debug("Neo4j unavailable — mock visualization (offline) for %s.", uid)
        return _mock_visualization_graph(uid, reason="offline")

    query_str = """
    MATCH (c:Chunk {user_id: $user_id})
    WITH c LIMIT 50
    OPTIONAL MATCH (c)-[r]-(other)
    RETURN
        elementId(c) AS source_id,
        c.name AS source_name,
        labels(c) AS source_labels,
        properties(c) AS source_props,
        elementId(other) AS target_id,
        other.name AS target_name,
        labels(other) AS target_labels,
        properties(other) AS target_props,
        type(r) AS rel_type,
        properties(r) AS rel_props
    LIMIT 120
    """
    records = run_cypher(query_str, {"user_id": uid})

    if not records:
        if not _neo4j_reachable():
            return _mock_visualization_graph(uid, reason="offline")
        logger.debug("No chunks for %s — mock visualization (no_documents).", uid)
        return _mock_visualization_graph(uid, reason="no_documents")

    return _assemble_visualization(records, uid)
