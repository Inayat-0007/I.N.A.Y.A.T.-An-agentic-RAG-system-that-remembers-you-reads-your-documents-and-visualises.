"""CI smoke test suite for I.N.A.Y.A.T.

Validates:
  1. All core modules import without syntax / dependency errors.
  2. Environment schema parses correctly.
  3. Health monitor instantiates.
  4. (When secrets are present) services are reachable.

Usage (local and CI):
    python tests/smoke_test.py          # exits 0 on pass, 1 on fail

Do not use pytest for CI; unittest via __main__ is the supported runner.
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

    def test_import_settings(self) -> None:
        import core.settings  # noqa: F401

    def test_import_identity(self) -> None:
        import core.identity  # noqa: F401

    def test_import_observability(self) -> None:
        import core.observability  # noqa: F401

    def test_import_schemas(self) -> None:
        import core.schemas  # noqa: F401

    def test_import_conversation(self) -> None:
        import core.conversation  # noqa: F401

    def test_import_ingest(self) -> None:
        import core.ingest  # noqa: F401

    def test_import_compat(self) -> None:
        import core.compat  # noqa: F401


class TestBackwardsCompatibility(unittest.TestCase):
    """HOW_TO_FIX §0.3 — legacy contracts must keep working."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("GEMINI_API_KEY", "test-smoke-key")
        from core.settings import clear_settings_cache

        clear_settings_cache()

    def test_query_legacy_signature_returns_str(self) -> None:
        from unittest.mock import MagicMock, patch

        with patch("core.agent.configure_llama_settings"), patch(
            "core.agent.get_index", return_value=None
        ), patch("core.agent.get_gemini_llm") as mock_llm:
            mock_llm.return_value.complete.return_value = "legacy ok"
            from core.agent import query

            answer = query("Hello?", user_id="default", memory_context="")
            self.assertIsInstance(answer, str)
            self.assertEqual(answer, "legacy ok")

    def test_mem0_user_id_not_renamed(self) -> None:
        from core.compat import mem0_user_id

        self.assertEqual(mem0_user_id("Rahul"), "Rahul")
        self.assertEqual(mem0_user_id("  Moham  "), "Moham")

    def test_breaker_forced_open_requires_demo_mode(self) -> None:
        from core.resilience import CircuitBreaker, DemoModeRequired, set_breaker_forced_open
        from core.settings import clear_settings_cache, get_settings

        os.environ["INAYAT_DEMO_MODE"] = "false"
        clear_settings_cache()
        self.assertFalse(get_settings().demo_mode)

        cb = CircuitBreaker()
        with self.assertRaises(DemoModeRequired):
            set_breaker_forced_open(cb, True, service="Mem0")

        os.environ["INAYAT_DEMO_MODE"] = "true"
        clear_settings_cache()
        set_breaker_forced_open(cb, True, service="Mem0")
        self.assertTrue(cb.forced_open)
        set_breaker_forced_open(cb, False, service="Mem0")
        self.assertFalse(cb.forced_open)

    def test_clear_stale_forced_breakers_when_demo_off(self) -> None:
        from core.resilience import CircuitBreaker, clear_stale_forced_breakers, set_breaker_forced_open
        from core.settings import clear_settings_cache

        os.environ["INAYAT_DEMO_MODE"] = "true"
        clear_settings_cache()
        import core.memory as mem

        set_breaker_forced_open(mem._cb, True, service="Mem0")
        self.assertTrue(mem._cb.forced_open)

        os.environ["INAYAT_DEMO_MODE"] = "false"
        clear_settings_cache()
        clear_stale_forced_breakers()
        self.assertFalse(mem._cb.forced_open)

        os.environ["INAYAT_DEMO_MODE"] = "true"
        clear_settings_cache()


class TestIdentity(unittest.TestCase):
    """Verify user id sanitization."""

    def test_parse_valid_user_id(self) -> None:
        from core.identity import UserId

        self.assertEqual(UserId.parse("Alice").value, "Alice")
        self.assertEqual(UserId.parse("Moham").value, "Moham")
        self.assertEqual(UserId.parse("default").value, "default")
        self.assertEqual(UserId.parse("INAYAT_HUSSAIN").value, "INAYAT_HUSSAIN")
        self.assertNotEqual(
            UserId.parse("INAYAT_HUSSAIN").value, UserId.parse("Inayat").value
        )

    def test_reject_spaces_in_user_id(self) -> None:
        from core.identity import InvalidUserId, UserId

        with self.assertRaises(InvalidUserId):
            UserId.parse("Inayat Hussain")

    def test_reject_path_traversal(self) -> None:
        from core.identity import InvalidUserId, UserId

        with self.assertRaises(InvalidUserId):
            UserId.parse("../etc")
        with self.assertRaises(InvalidUserId):
            UserId.parse("alice/bob")


class TestSettings(unittest.TestCase):
    """InayatSettings validation (HOW_TO_FIX §3.1)."""

    def setUp(self) -> None:
        self._prev_gemini_key = os.environ.get("GEMINI_API_KEY")
        os.environ["GEMINI_API_KEY"] = "test-settings-key"
        from core.settings import clear_settings_cache

        clear_settings_cache()

    def tearDown(self) -> None:
        if self._prev_gemini_key is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = self._prev_gemini_key
        os.environ.pop("INAYAT_CHUNK_SIZE", None)
        os.environ.pop("INAYAT_CHUNK_OVERLAP", None)
        from core.settings import clear_settings_cache

        clear_settings_cache()

    def test_defaults_include_mmr_off(self) -> None:
        from core.settings import get_settings

        settings = get_settings()
        self.assertFalse(settings.mmr_enabled)
        self.assertEqual(settings.mmr_lambda, 0.7)
        self.assertEqual(settings.chunk_size, 512)
        self.assertEqual(settings.chunk_overlap, 64)
        self.assertFalse(settings.allow_empty_from_existing)
        self.assertTrue(settings.sync_ingest)
        self.assertEqual(settings.api_key, "")

    def test_chunk_overlap_must_be_less_than_chunk_size(self) -> None:
        from pydantic import ValidationError

        from core.settings import clear_settings_cache, get_settings

        os.environ["INAYAT_CHUNK_SIZE"] = "512"
        os.environ["INAYAT_CHUNK_OVERLAP"] = "512"
        clear_settings_cache()

        with self.assertRaises(ValidationError):
            get_settings()


class TestSchemas(unittest.TestCase):
    """Typed query contracts (HOW_TO_FIX §3.3)."""

    def test_query_input_coerces_user_id(self) -> None:
        from core.identity import UserId
        from core.schemas import QueryInput

        inp = QueryInput.from_raw("Hello?", user_id="demo_user")
        self.assertIsInstance(inp.user_id, UserId)
        self.assertEqual(inp.resolved_user().value, "demo_user")


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

    def test_circuit_breaker_half_open_single_probe(self) -> None:
        """Only one probe request should pass in HALF_OPEN state."""
        import time
        from core.resilience import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.05)
        cb.record_failure()
        self.assertFalse(cb.allow_request())
        time.sleep(0.06)  # Wait for recovery timeout
        # First probe should be allowed
        self.assertTrue(cb.allow_request())
        # Second concurrent probe should be blocked
        self.assertFalse(cb.allow_request())
        # After success, should be fully open again
        cb.record_success()
        self.assertTrue(cb.allow_request())

    def test_circuit_breaker_thread_safety(self) -> None:
        """Concurrent record_failure calls should not corrupt state."""
        import threading
        from core.resilience import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=100, recovery_timeout=60)
        errors = []

        def hammer():
            try:
                for _ in range(50):
                    cb.record_failure()
                    cb.allow_request()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=hammer) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(errors), 0)


class TestLiveServices(unittest.TestCase):
    """Integration checks — skipped when API keys are absent."""

    def test_gemini_ping(self) -> None:
        key = os.getenv("GEMINI_API_KEY")
        if not key or "dummy" in key.lower() or key.startswith("test-"):
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


class TestFailureDesign(unittest.TestCase):
    """Verify section 0.2 failure-mode behaviors."""

    def test_graph_node_user_filter(self) -> None:
        from core.graph_store import _node_allowed_for_user

        self.assertTrue(
            _node_allowed_for_user(["Chunk"], {"user_id": "alice"}, "alice")
        )
        self.assertFalse(
            _node_allowed_for_user(["Chunk"], {"user_id": "bob"}, "alice")
        )
        self.assertTrue(_node_allowed_for_user(["Entity"], {}, "alice"))
        self.assertFalse(
            _node_allowed_for_user(["Entity"], {"user_id": "bob"}, "alice")
        )

    def test_assemble_strips_foreign_chunks(self) -> None:
        from core.graph_store import _assemble_visualization

        records = [
            {
                "source_id": "c1",
                "source_name": "Alice chunk",
                "source_labels": ["Chunk"],
                "source_props": {"user_id": "alice", "file_name": "a.pdf"},
                "target_id": "e1",
                "target_name": "SharedEntity",
                "target_labels": ["Entity"],
                "target_props": {},
                "rel_type": "MENTIONS",
                "rel_props": {},
            },
            {
                "source_id": "c2",
                "source_name": "Bob chunk",
                "source_labels": ["Chunk"],
                "source_props": {"user_id": "bob", "file_name": "b.pdf"},
                "target_id": "e1",
                "target_name": "SharedEntity",
                "target_labels": ["Entity"],
                "target_props": {},
                "rel_type": "MENTIONS",
                "rel_props": {},
            },
        ]
        graph = _assemble_visualization(records, "alice")
        ids = {n["id"] for n in graph["nodes"]}
        self.assertIn("c1", ids)
        self.assertNotIn("c2", ids)
        self.assertNotIn("e1", ids)
        self.assertFalse(graph["is_mock"])
        self.assertIsNone(graph.get("mock_reason"))

    def test_assemble_keeps_isolated_user_chunks(self) -> None:
        from core.graph_store import _assemble_visualization

        records = [
            {
                "source_id": "c1",
                "source_name": None,
                "source_labels": ["Chunk"],
                "source_props": {"user_id": "alice", "file_name": "a.pdf"},
                "target_id": None,
                "target_name": None,
                "target_labels": None,
                "target_props": None,
                "rel_type": None,
                "rel_props": None,
            }
        ]
        graph = _assemble_visualization(records, "alice")
        self.assertFalse(graph["is_mock"])
        self.assertEqual(len(graph["nodes"]), 1)

    def test_assemble_chunk_label_from_document_text(self) -> None:
        from core.graph_store import _assemble_visualization

        records = [
            {
                "source_id": "c1",
                "source_name": None,
                "source_labels": ["__Node__", "Chunk"],
                "source_props": {
                    "user_id": "alice",
                    "file_name": "report.pdf",
                    "text": "The CEO of INAYAT is Aisha Khan.\nMore context.",
                    "embedding": [0.1, 0.2],
                },
                "target_id": None,
                "target_name": None,
                "target_labels": None,
                "target_props": None,
                "rel_type": None,
                "rel_props": None,
            }
        ]
        graph = _assemble_visualization(records, "alice")
        self.assertFalse(graph["is_mock"])
        node = graph["nodes"][0]
        self.assertEqual(node["group"], "Chunk")
        self.assertIn("CEO of INAYAT", node["label"])
        self.assertNotIn("__Node__", node["label"])
        self.assertIn("text", node["properties"])
        self.assertNotIn("embedding", node["properties"])

    def test_empty_user_mock_is_no_documents_not_offline(self) -> None:
        from core.graph_store import _assemble_visualization, _mock_visualization_graph

        graph = _assemble_visualization([], "INAYAT_TEST_1")
        self.assertTrue(graph["is_mock"])
        self.assertEqual(graph["mock_reason"], "no_documents")
        self.assertEqual(graph["nodes"], [])
        self.assertEqual(graph["edges"], [])
        offline = _mock_visualization_graph("INAYAT_TEST_1", reason="offline")
        self.assertEqual(offline["mock_reason"], "offline")
        self.assertEqual(offline["nodes"], [])

    def test_index_build_in_progress(self) -> None:
        from core import ingest as ingest_mod
        from core.exceptions import IndexBuildInProgress
        from core.ingest import schedule_index_build

        os.environ.setdefault("GEMINI_API_KEY", "test-smoke-key")
        from core.settings import clear_settings_cache

        clear_settings_cache()

        with ingest_mod._jobs_lock:
            ingest_mod._index_jobs["default"] = ingest_mod._IndexJob(
                status="building", job_id="existing-job", updated_at=0.0
            )

        with self.assertRaises(IndexBuildInProgress) as ctx:
            schedule_index_build("default")
        self.assertEqual(ctx.exception.job_id, "existing-job")

        with ingest_mod._jobs_lock:
            ingest_mod._index_jobs.pop("default", None)

    def test_upload_size_limit_message(self) -> None:
        os.environ.setdefault("GEMINI_API_KEY", "test-smoke-key")
        from core.settings import clear_settings_cache, get_settings

        clear_settings_cache()
        from core.ingest import save_uploads

        huge = b"%PDF-1.4\n" + (b"x" * (get_settings().max_upload_bytes + 1))
        with self.assertRaises(ValueError) as ctx:
            save_uploads("default", [("big.pdf", huge)])
        self.assertIn("exceeds maximum upload size", str(ctx.exception))


from unittest.mock import patch, MagicMock


class TestAgentPipeline(unittest.TestCase):
    """Verify agent query pipeline with mocked services."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("GEMINI_API_KEY", "test-smoke-key")
        from core.settings import clear_settings_cache

        clear_settings_cache()

    @patch("core.agent.configure_llama_settings")
    @patch("core.agent.retrieve_user_chunks")
    @patch("core.agent.get_gemini_llm")
    def test_query_rag_success(self, mock_get_llm, mock_retrieve, _mock_configure) -> None:
        mock_retrieve.return_value = [
            {"text": "AI is intelligence in machines.", "file_name": "notes.txt"}
        ]
        mock_llm = MagicMock()
        mock_llm.complete.return_value = "Mocked RAG response about AI."
        mock_get_llm.return_value = mock_llm

        from core.agent import query_detailed
        from core.schemas import QueryInput

        result = query_detailed(QueryInput.from_raw("What is AI?"))
        self.assertEqual(result.route, "rag")
        self.assertGreater(result.source_count, 0)
        self.assertEqual(result.answer, "Mocked RAG response about AI.")
        mock_llm.complete.assert_called_once()

    @patch("core.agent.configure_llama_settings")
    @patch("core.agent.retrieve_user_chunks")
    @patch("core.agent.get_gemini_llm")
    def test_query_detailed_empty_sources_routes_llm(
        self, mock_get_llm, mock_retrieve, _mock_configure
    ) -> None:
        mock_retrieve.return_value = []

        mock_llm = MagicMock()
        mock_llm.complete.return_value = "LLM answer."
        mock_get_llm.return_value = mock_llm

        from core.agent import query_detailed
        from core.schemas import QueryInput

        result = query_detailed(QueryInput.from_raw("What is AI?"))
        self.assertEqual(result.route, "llm")
        mock_llm.complete.assert_called_once()

    @patch("core.agent.configure_llama_settings")
    @patch("core.agent.retrieve_user_chunks")
    @patch("core.agent.get_gemini_llm")
    def test_query_rag_fails_llm_fallback(
        self, mock_get_llm, mock_retrieve, _mock_configure
    ) -> None:
        mock_retrieve.return_value = []

        mock_llm = MagicMock()
        mock_llm.complete.return_value = "Mocked LLM fallback response."
        mock_get_llm.return_value = mock_llm

        from core.agent import query

        ans = query("Hello?", memory_context="")
        self.assertEqual(ans, "Mocked LLM fallback response.")
        mock_llm.complete.assert_called_once()

    @patch("core.agent.configure_llama_settings")
    @patch("core.agent.retrieve_user_chunks")
    @patch("core.agent.get_gemini_llm")
    def test_query_rag_keeps_answer_when_sources_hedge(
        self, mock_get_llm, mock_retrieve, _mock_configure
    ) -> None:
        mock_retrieve.return_value = [
            {"text": "The CEO is named.", "file_name": "facts.txt"}
        ]
        mock_llm = MagicMock()
        mock_llm.complete.return_value = (
            "The document does not contain a salary figure, but the CEO is named."
        )
        mock_get_llm.return_value = mock_llm

        from core.agent import query_detailed
        from core.schemas import QueryInput

        result = query_detailed(QueryInput.from_raw("Who is the CEO?"))
        self.assertEqual(result.route, "rag")
        self.assertGreater(result.source_count, 0)
        self.assertEqual(mock_get_llm.call_count, 1)


class TestObservability(unittest.TestCase):
    """HOW_TO_FIX §7 — structured query logging."""

    def test_log_query_event_format(self) -> None:
        from core.observability import log_query_event, set_request_id

        set_request_id("test-rid-123")
        with self.assertLogs("inayat", level="INFO") as captured:
            log_query_event(
                user_id="alice",
                route="rag",
                latency_ms=12.5,
                source_count=2,
                mem0_ok=True,
                neo4j_ok=False,
                rag_ms=8.0,
            )
        line = captured.output[-1]
        self.assertIn("event=query", line)
        self.assertIn("user_id=alice", line)
        self.assertIn("route=rag", line)
        self.assertIn("mem0_ok=true", line)
        self.assertIn("neo4j_ok=false", line)
        self.assertNotIn("GEMINI", line)


class TestMemoryContext(unittest.TestCase):
    """HOW_TO_FIX §4.1 — search + get_all merge with cap."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("GEMINI_API_KEY", "test-smoke-key")
        from core.settings import clear_settings_cache

        clear_settings_cache()

    @patch("core.memory.get_memories")
    @patch("core.memory.search_memories")
    def test_build_memory_context_merges_and_caps(
        self, mock_search, mock_get
    ) -> None:
        mock_search.return_value = ["User likes tea"]
        mock_get.return_value = ["User likes tea", "User is in Pune"]
        from core.memory import build_memory_context

        ctx, lines = build_memory_context("demo_user", "What do I like?")
        self.assertIn("tea", ctx)
        self.assertIn("Pune", ctx)
        self.assertEqual(len(lines), 2)

    @patch("core.memory.get_memories")
    @patch("core.memory.search_memories")
    def test_build_memory_context_search_failure_falls_back(
        self, mock_search, mock_get
    ) -> None:
        mock_search.side_effect = RuntimeError("mem0 down")
        mock_get.return_value = ["fallback fact"]
        from core.memory import build_memory_context

        ctx, lines = build_memory_context("demo_user", "hello")
        self.assertIn("fallback fact", ctx)
        self.assertEqual(lines, ["fallback fact"])


class TestIngestIsolation(unittest.TestCase):
    """HOW_TO_FIX §4.4 — empty folder does not attach shared graph."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("GEMINI_API_KEY", "test-smoke-key")
        from core.settings import clear_settings_cache

        clear_settings_cache()

    def test_get_index_skips_from_existing_when_empty(self) -> None:
        from core.ingest import get_index

        index = get_index("empty_user_no_docs")
        self.assertIsNone(index)

    def test_save_uploads_rejects_fake_pdf(self) -> None:
        from core.ingest import save_uploads

        with self.assertRaises(ValueError) as ctx:
            save_uploads("default", [("not.pdf", b"this is not a pdf")])
        self.assertIn("valid PDF", str(ctx.exception))

    def test_user_has_documents_false_for_empty_profile(self) -> None:
        from core.ingest import user_has_documents

        self.assertFalse(user_has_documents("no_such_profile_xyz"))

    def test_pending_files_skips_manifest_entries(self) -> None:
        import json
        import tempfile
        from pathlib import Path

        from core.ingest import _file_fingerprint, _pending_files, _write_manifest

        with tempfile.TemporaryDirectory() as tmp:
            user_dir = Path(tmp)
            old = user_dir / "old.txt"
            new = user_dir / "new.txt"
            old.write_text("already indexed", encoding="utf-8")
            new.write_text("needs indexing", encoding="utf-8")
            _write_manifest(user_dir, {"old.txt": _file_fingerprint(old)})
            pending, skipped = _pending_files(user_dir)
            self.assertEqual([p.name for p in pending], ["new.txt"])
            self.assertEqual([p.name for p in skipped], ["old.txt"])
            pending_only, _ = _pending_files(user_dir, only_files=["new.txt"])
            self.assertEqual([p.name for p in pending_only], ["new.txt"])
            manifest = json.loads((user_dir / ".indexed.json").read_text(encoding="utf-8"))
            self.assertIn("old.txt", manifest["files"])

    def test_load_documents_stamps_user_id_on_txt(self) -> None:
        import tempfile
        from pathlib import Path

        from core.ingest import _load_documents

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "note.txt"
            path.write_text("INAYAT master data sample", encoding="utf-8")
            docs = _load_documents([path], "INAYAT_TEST_1")
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].metadata.get("user_id"), "INAYAT_TEST_1")
        self.assertIn("master data", docs[0].text.lower())

    def test_list_user_documents_returns_saved_files(self) -> None:
        from core.ingest import list_user_documents, save_uploads, unindexed_document_names

        saved = save_uploads(
            "smoke_list_docs",
            [("note.txt", b"hello ingest")],
            overwrite=True,
        )
        self.assertEqual(saved, ["note.txt"])
        rows = list_user_documents("smoke_list_docs")
        names = {row["name"] for row in rows}
        self.assertIn("note.txt", names)
        self.assertIn("note.txt", unindexed_document_names("smoke_list_docs"))


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestImports))
    suite.addTests(loader.loadTestsFromTestCase(TestIdentity))
    suite.addTests(loader.loadTestsFromTestCase(TestSettings))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemas))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironment))
    suite.addTests(loader.loadTestsFromTestCase(TestHealthMonitor))
    suite.addTests(loader.loadTestsFromTestCase(TestResilience))
    suite.addTests(loader.loadTestsFromTestCase(TestLiveServices))
    suite.addTests(loader.loadTestsFromTestCase(TestBackwardsCompatibility))
    suite.addTests(loader.loadTestsFromTestCase(TestFailureDesign))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestObservability))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryContext))
    suite.addTests(loader.loadTestsFromTestCase(TestIngestIsolation))
    _tests_dir = os.path.dirname(os.path.abspath(__file__))
    if _tests_dir not in sys.path:
        sys.path.insert(0, _tests_dir)
    from test_api_contract import TestApiContract

    suite.addTests(loader.loadTestsFromTestCase(TestApiContract))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
