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

    out = safe_execute(_run, fallback=[])
    if out == []:
        _cb.record_failure()
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
