"""Startup validation and service warm-up.

Orchestrates environment loading, logging, and health probes at boot.
"""

from __future__ import annotations

import atexit
import logging
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from pydantic import ValidationError

from core.health import HealthMonitor
from core.logging_config import setup_logging
from core.settings import clear_settings_cache, get_settings

logger = logging.getLogger("inayat")

CRITICAL_VARS = ["GEMINI_API_KEY"]
RECOMMENDED_VARS = [
    "MEM0_API_KEY",
    "NEO4J_URI",
    "NEO4J_USERNAME",
    "NEO4J_PASSWORD",
]


def load_env() -> None:
    """Load ``.env`` file into ``os.environ`` and refresh settings cache."""
    load_dotenv(override=False)
    clear_settings_cache()


def validate_env() -> Tuple[bool, List[str], List[str]]:
    """Check that required and recommended env vars are present.

    Returns:
        Tuple of (critical_ok, missing_critical, missing_recommended).
    """
    try:
        settings = get_settings()
    except ValidationError:
        return False, list(CRITICAL_VARS), list(RECOMMENDED_VARS)

    missing_recommended = settings.missing_recommended_vars()
    if missing_recommended:
        logger.warning(
            "Recommended env vars missing (features degraded): %s",
            ", ".join(missing_recommended),
        )

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

    monitor = HealthMonitor()
    statuses = monitor.run_all()

    from core.graph_store import close_driver

    atexit.register(close_driver)

    logger.info("Startup complete.  Health: %s", statuses)
    return True, statuses, warnings


def enforce_critical_env_or_exit() -> None:
    """Refuse process start when critical configuration is missing.

    Prints a clear error to stderr and exits with code 1.
    """
    import sys

    load_env()
    setup_logging()
    ok, missing_crit, _ = validate_env()
    if ok:
        return

    message = (
        "FATAL: Cannot start I.N.A.Y.A.T. — missing critical environment variable(s): "
        f"{', '.join(missing_crit)}. "
        "Set GEMINI_API_KEY in your .env file or environment."
    )
    print(message, file=sys.stderr)
    sys.exit(1)
