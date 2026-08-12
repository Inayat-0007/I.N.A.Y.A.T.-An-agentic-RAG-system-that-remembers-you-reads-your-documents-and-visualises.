"""Neo4j AuraDB driver and Cypher query wrapper.

Manages a singleton ``neo4j.Driver`` connection pool and exposes a
resilient ``run_cypher`` helper.  Also provides the
``get_neo4j_property_graph_store`` factory used by the LlamaIndex
``PropertyGraphIndex``.
"""

import logging
import threading
from typing import Any, Dict, List, Optional

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


def _mock_visualization_graph(user_id: str = "default") -> dict:
    """Return profile-customised demo graph when live data is unavailable."""
    prefix = f"{user_id}'s " if user_id and user_id.lower() != "default" else ""
    nodes = [
        {
            "id": 1,
            "label": f"{prefix}I.N.A.Y.A.T. Agent",
            "group": "Agent",
            "properties": {
                "Role": f"Core Agent Coordinator for {user_id or 'User'}",
                "Description": "Main reasoning agent which coordinates between user profiles, long-term memory (Mem0), and property graph storage (Neo4j RAG) using Google Gemini.",
            },
        },
        {
            "id": 2,
            "label": "Gemini Flash Lite",
            "group": "LLM",
            "properties": {
                "Model": "gemini-flash-lite-latest",
                "Role": "Generative Language Model",
                "Provider": "Google Gemini API via Google AI Studio",
                "Wrapper": "ResilientGoogleGenAI for self-healing completions.",
            },
        },
        {
            "id": 3,
            "label": f"{prefix}Mem0 Cloud Memory",
            "group": "Memory",
            "properties": {
                "API": "Mem0 Cloud API",
                "Role": "Long-Term Persistent Memory",
                "Purpose": f"Saves and retrieves facts about {user_id or 'user'} preferences and history across sessions.",
            },
        },
        {
            "id": 4,
            "label": "Neo4j AuraDB Graph",
            "group": "GraphStore",
            "properties": {
                "Store": "Neo4j AuraDB Cloud",
                "Role": "Property Graph Store",
                "Structure": f"Entity-Relationship graph index built with LlamaIndex PropertyGraphIndex from data/documents/{user_id or 'user'}.",
            },
        },
        {
            "id": 5,
            "label": "Circuit Breaker",
            "group": "Resilience",
            "properties": {
                "Class": "CircuitBreaker",
                "Role": "Self-Healing Guard",
                "Status": "Closed (Normal Operations)",
                "Failure Threshold": "3 consecutive errors",
                "Recovery Time": "60 seconds",
            },
        },
        {
            "id": 6,
            "label": f"{user_id or 'User'} Session Profile",
            "group": "User",
            "properties": {
                "Source": "Streamlit Session State",
                "Role": "Active User Session Profile",
                "Scope": f"Tracks {user_id or 'user'} name, messages, and state parameters.",
            },
        },
    ]
    edges = [
        {
            "from": 6,
            "to": 1,
            "label": "inputs query",
            "properties": {
                "Interaction": "Sends natural language queries and documents to the agent."
            },
        },
        {
            "from": 1,
            "to": 3,
            "label": "fetches memories",
            "properties": {
                "Operation": "Extracts context-relevant memories for the active user name."
            },
        },
        {
            "from": 1,
            "to": 4,
            "label": "queries facts",
            "properties": {
                "Operation": "Executes vector search and cypher queries on entities and chunks."
            },
        },
        {
            "from": 1,
            "to": 2,
            "label": "completes prompt",
            "properties": {
                "Operation": "Submits final prompt constructed from user query, memories, and RAG chunks."
            },
        },
        {
            "from": 3,
            "to": 5,
            "label": "monitored by",
            "properties": {
                "Mechanism": "Wraps API requests. Opens circuit if requests fail consistently."
            },
        },
        {
            "from": 4,
            "to": 5,
            "label": "monitored by",
            "properties": {
                "Mechanism": "Wraps Cypher queries. Opens circuit if AuraDB goes offline."
            },
        },
    ]
    return {"nodes": nodes, "edges": edges, "is_mock": True}


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
            if key in ("embedding", "_node_content"):
                continue
            if key == "text" and isinstance(value, str) and len(value) > 1000:
                cleaned[key] = value[:1000] + "..."
            else:
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
        if not s_id or not t_id:
            continue
        s_props = clean_props(rec.get("source_props"))
        t_props = clean_props(rec.get("target_props"))
        s_labels = rec.get("source_labels") or ["Entity"]
        t_labels = rec.get("target_labels") or ["Entity"]
        raw_nodes[s_id] = {
            "labels": s_labels,
            "props": s_props,
            "name": rec.get("source_name"),
        }
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
        _touch(s_id)
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
        return _mock_visualization_graph(user_id)

    nodes: dict = {}
    edges: list = []
    for nid in allowed:
        node = raw_nodes[nid]
        labels = node["labels"] or ["Entity"]
        label = labels[0]
        props = node["props"]
        name = node["name"]
        if not name:
            if label == "Chunk" and props.get("file_name"):
                name = f"Chunk: {props.get('file_name')}"
            else:
                name = f"{label} ({str(nid)[:6]})"
        nodes[nid] = {
            "id": nid,
            "label": name,
            "group": label,
            "properties": props,
            "title": f"<b>{label}</b>: {name}",
        }

    for edge in raw_edges:
        if edge["from"] in allowed and edge["to"] in allowed:
            edges.append(edge)

    if not nodes:
        return _mock_visualization_graph(user_id)
    return {"nodes": list(nodes.values()), "edges": edges, "is_mock": False}


def get_visualization_data(user_id: str = "default") -> dict:
    """Retrieve user-scoped nodes/edges; mock graph when Neo4j is unavailable."""
    uid = UserId.parse(user_id).value
    if not _cb.allow_request():
        logger.debug("Neo4j circuit OPEN — returning mock visualization for %s.", uid)
        return _mock_visualization_graph(uid)

    query_str = """
    MATCH (c:Chunk {user_id: $user_id})
    MATCH (s)-[r]->(t)
    WHERE (s = c OR t = c)
       OR EXISTS { MATCH (c)-[*1..2]-(s) }
       OR EXISTS { MATCH (c)-[*1..2]-(t) }
    RETURN
        elementId(s) AS source_id,
        s.name AS source_name,
        labels(s) AS source_labels,
        properties(s) AS source_props,
        elementId(t) AS target_id,
        t.name AS target_name,
        labels(t) AS target_labels,
        properties(t) AS target_props,
        type(r) AS rel_type,
        properties(r) AS rel_props
    LIMIT 120
    """
    records = run_cypher(query_str, {"user_id": uid})

    if not records:
        return _mock_visualization_graph(uid)

    return _assemble_visualization(records, uid)
