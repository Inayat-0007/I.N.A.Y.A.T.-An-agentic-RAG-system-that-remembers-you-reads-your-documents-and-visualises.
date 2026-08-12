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
from core.settings import InayatSettings, get_settings

logger = logging.getLogger("inayat")

_driver: Optional[Driver] = None
_driver_lock = threading.Lock()
_cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)


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
    """Return True when a graph node may be shown for the given user."""
    label_list = labels or ["Entity"]
    if "Chunk" in label_list:
        return props.get("user_id") == user_id
    if "Entity" in label_list:
        return True
    node_user = props.get("user_id")
    return node_user in (None, user_id)


def get_visualization_data(user_id: str = "default") -> dict:
    """Retrieve user-scoped nodes/edges; mock graph when Neo4j is unavailable."""
    if not _cb.allow_request():
        logger.debug("Neo4j circuit OPEN — returning mock visualization for %s.", user_id)
        return _mock_visualization_graph(user_id)

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
    records = run_cypher(query_str, {"user_id": user_id})

    if not records:
        return _mock_visualization_graph(user_id)

    nodes: dict = {}
    edges: list = []

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

    for rec in records:
        s_id = rec.get("source_id")
        s_props = clean_props(rec.get("source_props"))
        s_labels = rec.get("source_labels", ["Entity"])
        s_label = s_labels[0] if s_labels else "Entity"

        t_id = rec.get("target_id")
        t_props = clean_props(rec.get("target_props"))
        t_labels = rec.get("target_labels", ["Entity"])
        t_label = t_labels[0] if t_labels else "Entity"

        if not _node_allowed_for_user(s_labels, s_props, user_id):
            continue
        if not _node_allowed_for_user(t_labels, t_props, user_id):
            continue

        s_name = rec.get("source_name")
        if not s_name:
            if s_label == "Chunk" and s_props.get("file_name"):
                s_name = f"Chunk: {s_props.get('file_name')}"
            else:
                s_name = f"{s_label} ({str(s_id)[:6]})"

        t_name = rec.get("target_name")
        if not t_name:
            if t_label == "Chunk" and t_props.get("file_name"):
                t_name = f"Chunk: {t_props.get('file_name')}"
            else:
                t_name = f"{t_label} ({str(t_id)[:6]})"

        rel_type = rec.get("rel_type") or "RELATED"
        rel_props = clean_props(rec.get("rel_props"))

        if s_id not in nodes:
            nodes[s_id] = {
                "id": s_id,
                "label": s_name,
                "group": s_label,
                "properties": s_props,
                "title": f"<b>{s_label}</b>: {s_name}",
            }
        if t_id not in nodes:
            nodes[t_id] = {
                "id": t_id,
                "label": t_name,
                "group": t_label,
                "properties": t_props,
                "title": f"<b>{t_label}</b>: {t_name}",
            }

        edges.append(
            {"from": s_id, "to": t_id, "label": rel_type, "properties": rel_props}
        )

    if not nodes:
        return _mock_visualization_graph(user_id)

    return {"nodes": list(nodes.values()), "edges": edges, "is_mock": False}
