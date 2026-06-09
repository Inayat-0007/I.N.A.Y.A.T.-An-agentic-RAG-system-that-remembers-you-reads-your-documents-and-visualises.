"""Startup validation and service warm-up.

Meant to be called once at application boot (top of ``app.py``).
Validates that critical environment variables exist and optionally runs
a full health sweep.
"""

import os
import sys
import logging
from typing import Tuple, List, Dict

from dotenv import load_dotenv

from core.logging_config import setup_logging
from core.health import HealthMonitor

logger = logging.getLogger("inayat")

# Environment variables that MUST exist for the app to function at all
CRITICAL_VARS = [
    "GEMINI_API_KEY",
]

# Variables that are strongly recommended but non-fatal if missing
RECOMMENDED_VARS = [
    "MEM0_API_KEY",
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
]


def load_env() -> None:
    """Load ``.env`` file into ``os.environ``.

    Call this before any other startup step.
    """
    load_dotenv(override=False)


def validate_env() -> Tuple[bool, List[str], List[str]]:
    """Check that required and recommended env vars are present.

    Returns:
        Tuple of (critical_ok, missing_critical, missing_recommended).
    """
    missing_critical = [v for v in CRITICAL_VARS if not os.getenv(v)]
    missing_recommended = [v for v in RECOMMENDED_VARS if not os.getenv(v)]

    if missing_recommended:
        logger.warning(
            "Recommended env vars missing (features degraded): %s",
            ", ".join(missing_recommended),
        )

    if missing_critical:
        logger.error(
            "CRITICAL env vars missing — app cannot start: %s",
            ", ".join(missing_critical),
        )
        return False, missing_critical, missing_recommended

    return True, [], missing_recommended


def run_startup() -> Tuple[bool, Dict[str, str], List[str]]:
    """Full startup sequence.

    1. Load ``.env``.
    2. Initialise the logger.
    3. Validate environment.
    4. Run health checks.

    Returns:
        Tuple of (ok, health_statuses, warnings).
    """
    load_env()
    setup_logging()

    ok, missing_crit, missing_rec = validate_env()
    warnings: List[str] = []

    if not ok:
        return False, {}, [f"Missing critical: {', '.join(missing_crit)}"]

    if missing_rec:
        warnings.append(f"Missing recommended vars: {', '.join(missing_rec)}")

    # Run health probes
    monitor = HealthMonitor()
    statuses = monitor.run_all()

    logger.info("Startup complete.  Health: %s", statuses)
    return True, statuses, warnings
