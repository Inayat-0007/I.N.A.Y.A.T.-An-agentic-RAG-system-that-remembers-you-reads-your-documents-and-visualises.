"""CI smoke test suite for I.N.A.Y.A.T.

Validates:
  1. All core modules import without syntax / dependency errors.
  2. Environment schema parses correctly.
  3. Health monitor instantiates.
  4. (When secrets are present) services are reachable.

Usage (local):
    python -m pytest tests/smoke_test.py -v

Usage (CI):
    python tests/smoke_test.py          # exits 0 on pass, 1 on fail
"""

import os
import sys
import unittest

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.startup import load_env

# Load .env if present (CI uses GitHub Secrets injected as real env vars)
load_env()


class TestImports(unittest.TestCase):
    """Verify every core module imports cleanly."""

    def test_import_resilience(self) -> None:
        import core.resilience  # noqa: F401

    def test_import_logging_config(self) -> None:
        import core.logging_config  # noqa: F401

    def test_import_llm_setup(self) -> None:
        import core.llm_setup  # noqa: F401

    def test_import_memory(self) -> None:
        import core.memory  # noqa: F401

    def test_import_graph_store(self) -> None:
        import core.graph_store  # noqa: F401

    def test_import_agent(self) -> None:
        import core.agent  # noqa: F401

    def test_import_health(self) -> None:
        import core.health  # noqa: F401

    def test_import_startup(self) -> None:
        import core.startup  # noqa: F401


class TestEnvironment(unittest.TestCase):
    """Verify environment parsing logic."""

    def test_validate_env_runs(self) -> None:
        from core.startup import validate_env

        ok, missing_crit, missing_rec = validate_env()
        # We don't assert ok=True because CI might not have all secrets
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(missing_crit, list)
        self.assertIsInstance(missing_rec, list)


class TestHealthMonitor(unittest.TestCase):
    """Verify health monitor initialises."""

    def test_instantiate(self) -> None:
        from core.health import HealthMonitor

        monitor = HealthMonitor()
        self.assertIn("gemini", monitor.status)
        self.assertIn("mem0", monitor.status)
        self.assertIn("neo4j", monitor.status)


class TestResilience(unittest.TestCase):
    """Verify resilience utilities work in isolation."""

    def test_safe_execute_success(self) -> None:
        from core.resilience import safe_execute

        result = safe_execute(lambda: 42, fallback=-1)
        self.assertEqual(result, 42)

    def test_safe_execute_fallback(self) -> None:
        from core.resilience import safe_execute

        def _boom() -> int:
            raise RuntimeError("test error")

        result = safe_execute(_boom, fallback=-1)
        self.assertEqual(result, -1)

    def test_circuit_breaker_opens(self) -> None:
        from core.resilience import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        self.assertTrue(cb.allow_request())
        cb.record_failure()
        self.assertTrue(cb.allow_request())  # still under threshold
        cb.record_failure()
        self.assertFalse(cb.allow_request())  # now OPEN

    def test_circuit_breaker_resets(self) -> None:
        from core.resilience import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        self.assertFalse(cb.allow_request())
        cb.record_success()
        self.assertTrue(cb.allow_request())


class TestLiveServices(unittest.TestCase):
    """Integration checks — skipped when API keys are absent."""

    def test_gemini_ping(self) -> None:
        key = os.getenv("GEMINI_API_KEY")
        if not key or "dummy" in key.lower():
            self.skipTest("GEMINI_API_KEY not set or is dummy")
        from core.llm_setup import ping_gemini

        self.assertTrue(ping_gemini())

    def test_mem0_ping(self) -> None:
        key = os.getenv("MEM0_API_KEY")
        if not key or "dummy" in key.lower():
            self.skipTest("MEM0_API_KEY not set or is dummy")
        from core.memory import ping_mem0

        self.assertTrue(ping_mem0())

    def test_neo4j_ping(self) -> None:
        uri = os.getenv("NEO4J_URI")
        pwd = os.getenv("NEO4J_PASSWORD")
        if not uri or not pwd or "dummy" in uri.lower() or "dummy" in pwd.lower():
            self.skipTest("NEO4J credentials not set or are dummy")
        from core.graph_store import ping_neo4j

        self.assertTrue(ping_neo4j())


from unittest.mock import patch, MagicMock


class TestAgentPipeline(unittest.TestCase):
    """Verify agent query pipeline with mocked services."""

    @patch("core.agent.get_index")
    @patch("core.agent.get_gemini_llm")
    def test_query_rag_success(self, mock_get_llm, mock_get_index) -> None:
        # Mock index query engine
        mock_index = MagicMock()
        mock_engine = MagicMock()

        # Create a mock response object that has source_nodes and returns the string
        mock_response = MagicMock()
        mock_response.source_nodes = [MagicMock()]
        mock_response.__str__.return_value = "Mocked RAG response about AI."

        mock_engine.query.return_value = mock_response
        mock_index.as_query_engine.return_value = mock_engine
        mock_get_index.return_value = mock_index

        from core.agent import query

        ans = query("What is AI?", memory_context="")
        self.assertEqual(ans, "Mocked RAG response about AI.")
        mock_engine.query.assert_called_once()

    @patch("core.agent.get_index")
    @patch("core.agent.get_gemini_llm")
    def test_query_rag_fails_llm_fallback(self, mock_get_llm, mock_get_index) -> None:
        # RAG fails (returns None)
        mock_get_index.return_value = None

        # LLM completes successfully
        mock_llm = MagicMock()
        mock_llm.complete.return_value = "Mocked LLM fallback response."
        mock_get_llm.return_value = mock_llm

        from core.agent import query

        ans = query("Hello?", memory_context="")
        self.assertEqual(ans, "Mocked LLM fallback response.")
        mock_llm.complete.assert_called_once()


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestImports))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironment))
    suite.addTests(loader.loadTestsFromTestCase(TestHealthMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestResilience))
    suite.addTests(loader.loadTestsFromTestCase(TestLiveServices))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentPipeline))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
