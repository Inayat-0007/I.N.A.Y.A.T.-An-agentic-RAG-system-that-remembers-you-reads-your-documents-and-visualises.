"""Neo4j AuraDB driver and Cypher query wrapper.

Manages a singleton ``neo4j.Driver`` connection pool and exposes a
resilient ``run_cypher`` helper.  Also provides the
``get_neo4j_property_graph_store`` factory used by the LlamaIndex
``PropertyGraphIndex``.
"""

import os
import logging
from typing import List, Dict, Any, Optional

from neo4j import GraphDatabase, Driver
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

from core.resilience import safe_execute, resilient_call, CircuitBreaker

logger = logging.getLogger("inayat")

_driver: Optional[Driver] = None
_cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def _get_credentials() -> tuple:
    """Return (uri, username, password) from env vars.

    Raises:
        ValueError: When mandatory vars are missing.
    """
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD")
    if not uri or not pwd:
        raise ValueError("NEO4J_URI / NEO4J_PASSWORD missing from environment.")
    return uri, user, pwd


def get_driver() -> Optional[Driver]:
    """Lazily create and return the global Neo4j driver.

    Returns:
        A ``Driver`` instance, or ``None`` when credentials are missing.
    """
    global _driver
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
        with driver.session() as session:
            result = session.run(query, parameters or {})
            records = [dict(record) for record in result]
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
    driver.verify_connectivity()
    logger.debug("Neo4j ping OK")
    return True


def get_visualization_data() -> dict:
    """Retrieve nodes and edges from Neo4j, falling back to a demo system graph on failure/empty."""
    query_str = """
    MATCH (s)-[r]->(t)
    RETURN 
        id(s) AS source_id, 
        s.name AS source_name, 
        labels(s) AS source_labels,
        id(t) AS target_id, 
        t.name AS target_name, 
        labels(t) AS target_labels,
        type(r) AS rel_type
    LIMIT 100
    """
    records = run_cypher(query_str)
    
    if records:
        nodes = {}
        edges = []
        for rec in records:
            s_id = rec.get("source_id")
            s_name = rec.get("source_name") or f"Node {s_id}"
            s_label = rec.get("source_labels", ["Entity"])[0] if rec.get("source_labels") else "Entity"
            
            t_id = rec.get("target_id")
            t_name = rec.get("target_name") or f"Node {t_id}"
            t_label = rec.get("target_labels", ["Entity"])[0] if rec.get("target_labels") else "Entity"
            
            rel_type = rec.get("rel_type") or "RELATED"
            
            if s_id not in nodes:
                nodes[s_id] = {"id": s_id, "label": s_name, "group": s_label}
            if t_id not in nodes:
                nodes[t_id] = {"id": t_id, "label": t_name, "group": t_label}
                
            edges.append({"from": s_id, "to": t_id, "label": rel_type})
            
        return {"nodes": list(nodes.values()), "edges": edges, "is_mock": False}
        
    # Mock fallback data
    nodes = [
        {"id": 1, "label": "I.N.A.Y.A.T. Agent", "group": "Agent"},
        {"id": 2, "label": "Gemini 1.5 Flash", "group": "LLM"},
        {"id": 3, "label": "Mem0 Cloud Memory", "group": "Memory"},
        {"id": 4, "label": "Neo4j AuraDB Graph", "group": "GraphStore"},
        {"id": 5, "label": "Circuit Breaker", "group": "Resilience"},
        {"id": 6, "label": "User Session Profile", "group": "User"},
    ]
    edges = [
        {"from": 6, "to": 1, "label": "inputs query"},
        {"from": 1, "to": 3, "label": "fetches memories"},
        {"from": 1, "to": 4, "label": "queries facts"},
        {"from": 1, "to": 2, "label": "completes prompt"},
        {"from": 3, "to": 5, "label": "monitored by"},
        {"from": 4, "to": 5, "label": "monitored by"},
    ]
    return {"nodes": nodes, "edges": edges, "is_mock": True}

