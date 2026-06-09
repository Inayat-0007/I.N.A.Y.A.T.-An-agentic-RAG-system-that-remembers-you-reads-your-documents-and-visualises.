"""Self-healing health monitor.

Provides a ``HealthMonitor`` class that checks connectivity to Gemini,
Mem0, and Neo4j.  The Streamlit sidebar displays these statuses, and the
startup validator uses them to decide whether to block launch.
"""

import logging
from typing import Dict

from core.resilience import safe_execute

logger = logging.getLogger("inayat")

# Status constants
UP = "🟢 Connected"
DOWN = "🔴 Unreachable"
DEGRADED = "🟡 Degraded"
UNCONFIGURED = "⚪ Not Configured"


class HealthMonitor:
    """Runs connectivity probes for each external service."""

    def __init__(self) -> None:
        self.status: Dict[str, str] = {
            "gemini": UNCONFIGURED,
            "mem0": UNCONFIGURED,
            "neo4j": UNCONFIGURED,
        }

    # ------------------------------------------------------------------ #
    # Individual checks
    # ------------------------------------------------------------------ #

    def check_gemini(self) -> str:
        """Ping Google Gemini and return a status string."""
        import os

        if not os.getenv("GEMINI_API_KEY"):
            return UNCONFIGURED

        from core.llm_setup import ping_gemini

        ok = safe_execute(ping_gemini, fallback=False)
        return UP if ok else DOWN

    def check_mem0(self) -> str:
        """Ping the Mem0 cloud API and return a status string."""
        import os

        if not os.getenv("MEM0_API_KEY"):
            return UNCONFIGURED

        from core.memory import ping_mem0

        ok = safe_execute(ping_mem0, fallback=False)
        return UP if ok else DOWN

    def check_neo4j(self) -> str:
        """Ping Neo4j AuraDB and return a status string."""
        import os

        if not os.getenv("NEO4J_URI") or not os.getenv("NEO4J_PASSWORD"):
            return UNCONFIGURED

        from core.graph_store import ping_neo4j

        ok = safe_execute(ping_neo4j, fallback=False)
        return UP if ok else DOWN

    # ------------------------------------------------------------------ #
    # Full sweep
    # ------------------------------------------------------------------ #

    def run_all(self) -> Dict[str, str]:
        """Execute every health check and update ``self.status``.

        Returns:
            Dict mapping service name → status emoji string.
        """
        self.status["gemini"] = self.check_gemini()
        self.status["mem0"] = self.check_mem0()
        self.status["neo4j"] = self.check_neo4j()

        logger.info(
            "Health check results — Gemini: %s | Mem0: %s | Neo4j: %s",
            self.status["gemini"],
            self.status["mem0"],
            self.status["neo4j"],
        )
        return self.status

    def all_critical_up(self) -> bool:
        """Return True when the minimum viable services (Gemini) are healthy."""
        return self.status.get("gemini") == UP
