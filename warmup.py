"""Manual pre-warm script for I.N.A.Y.A.T. services.

Run periodically (or via cron) to:
  • Keep Neo4j AuraDB's free-tier instance from pausing.
  • Verify all API keys are still valid.
  • Pre-load the PropertyGraphIndex so the first Streamlit query is fast.

Usage:
    python warmup.py
"""

import sys
import logging

from core.startup import load_env, validate_env
from core.logging_config import setup_logging
from core.health import HealthMonitor, UP
from core.resilience import safe_execute

logger: logging.Logger = None  # type: ignore


def warmup() -> bool:
    """Run the full warm-up sequence.

    Returns:
        True when all critical services are reachable.
    """
    global logger
    load_env()
    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("I.N.A.Y.A.T. PRE-WARM  —  starting")
    logger.info("=" * 60)

    # 1. Env check
    ok, missing_crit, missing_rec = validate_env()
    if not ok:
        logger.error("Warmup aborted — critical vars missing: %s", missing_crit)
        return False
    if missing_rec:
        logger.warning("Recommended vars missing (non-fatal): %s", missing_rec)

    # 2. Health probes
    monitor = HealthMonitor()
    statuses = monitor.run_all()
    for svc, status in statuses.items():
        logger.info("  %-8s -> %s", svc, status)

    # 3. Neo4j keepalive only — do not build an index for "default"
    from core.graph_store import run_cypher

    rows = safe_execute(lambda: run_cypher("RETURN 1 AS ping"), fallback=[])
    if rows and rows[0].get("ping") == 1:
        logger.info("  Neo4j keepalive query   -> OK")
    else:
        logger.warning("  Neo4j keepalive query   -> FAILED (instance may be paused)")

    from core.ingest import user_has_documents

    if user_has_documents("default"):
        from core.ingest import get_index

        idx = safe_execute(lambda: get_index("default"), fallback=None)
        if idx:
            logger.info("  PropertyGraphIndex      -> loaded for existing default profile")
        else:
            logger.warning("  PropertyGraphIndex      -> default profile exists but index failed")
    else:
        logger.info("  PropertyGraphIndex      -> skipped (no documents for default)")

    all_up = all(s == UP for s in statuses.values())
    logger.info("=" * 60)
    logger.info("Warmup complete.  All services UP: %s", all_up)
    logger.info("=" * 60)
    return all_up


if __name__ == "__main__":
    success = warmup()
    sys.exit(0 if success else 1)
