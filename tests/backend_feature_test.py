"""Comprehensive backend feature testing suite for I.N.A.Y.A.T.

Validates the full capability of:
  1. Startup Environment & Config (core/startup.py)
  2. LLM & Embedding Integrations (core/llm_setup.py)
  3. Resilience Toggles & Circuit Breakers (core/resilience.py)
  4. Memory Crud & Sync (core/memory.py)
  5. Neo4j Cypher & Graph Operations (core/graph_store.py)
  6. RAG Pipeline & Agent (core/agent.py)
  7. System Health Diagnostics (core/health.py)
"""

import os
import sys
import unittest
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.startup import load_env, validate_env, run_startup
load_env()

class TestBackendStartup(unittest.TestCase):
    """Verify startup initialization and configuration loading."""
    
    def test_startup_check(self):
        ok, health_status, warnings = run_startup()
        self.assertTrue(ok)
        self.assertIsInstance(health_status, dict)
        self.assertIn("gemini", health_status)
        self.assertIn("mem0", health_status)
        self.assertIn("neo4j", health_status)
        
    def test_env_validation(self):
        ok, missing_crit, missing_rec = validate_env()
        self.assertTrue(ok, f"Critical environment variable missing: {missing_crit}")
        self.assertEqual(len(missing_crit), 0)


class TestBackendLLM(unittest.TestCase):
    """Verify LLM and embedding configurations."""
    
    def test_gemini_llm_generation(self):
        from core.llm_setup import get_gemini_llm
        llm = get_gemini_llm()
        resp = llm.complete("Say the word 'verified' only.")
        self.assertIn("verified", resp.text.lower())
        
    def test_gemini_embeddings_retrieval(self):
        from core.llm_setup import get_gemini_embedding
        embedder = get_gemini_embedding()
        embedding = embedder.get_text_embedding("INAYAT project testing")
        self.assertEqual(len(embedding), 3072)  # standard gemini-embedding dimensions


class TestBackendResilience(unittest.TestCase):
    """Verify circuit breakers and fallback pipelines under failure scenarios."""
    
    def test_circuit_breaker_open_state(self):
        from core.resilience import CircuitBreaker
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)
        
        self.assertTrue(cb.allow_request())
        cb.record_failure()
        self.assertTrue(cb.allow_request())
        cb.record_failure()
        self.assertFalse(cb.allow_request())  # tripped
        
        # Test recovery after timeout
        time.sleep(0.6)
        self.assertEqual(cb.state, cb.HALF_OPEN)
        self.assertTrue(cb.allow_request())
        
        cb.record_success()
        self.assertEqual(cb.state, cb.CLOSED)
        self.assertTrue(cb.allow_request())


class TestBackendMemory(unittest.TestCase):
    """Verify Mem0 CRUD memory storage, retrieval, and removal."""
    
    def setUp(self):
        self.user_id = "test_backend_runner"
        from core.memory import clear_memories
        clear_memories(self.user_id)
        
    def tearDown(self):
        from core.memory import clear_memories
        clear_memories(self.user_id)
        
    def test_memory_crud_flow(self):
        from core.memory import add_memory, get_memories, search_memories
        
        # Add fact
        add_ok = add_memory(self.user_id, "I am testing the backend automation script.")
        self.assertTrue(add_ok)
        
        # Wait for mem0 cloud indexing with polling
        memories = []
        for _ in range(15):
            memories = get_memories(self.user_id)
            if memories:
                break
            time.sleep(1)
            
        # Retrieve memories assertions
        self.assertGreater(len(memories), 0)
        self.assertTrue(any("testing" in m.lower() for m in memories))
        
        # Search memories with polling
        matches = []
        for _ in range(15):
            matches = search_memories(self.user_id, "automation")
            if matches:
                break
            time.sleep(1)
            
        self.assertGreater(len(matches), 0)
        self.assertTrue(any("automation" in m.lower() for m in matches))


class TestBackendGraphStore(unittest.TestCase):
    """Verify Neo4j driver, Cypher execution, and Graph store mapping."""
    
    def test_run_cypher_nodes(self):
        from core.graph_store import run_cypher
        # Show databases count check
        res = run_cypher("SHOW DATABASES")
        self.assertGreater(len(res), 0)
        self.assertTrue(any(r.get("name") == os.getenv("NEO4J_USERNAME") for r in res))
        
    def test_graph_visualization_data_format(self):
        from core.graph_store import get_visualization_data
        data = get_visualization_data()
        self.assertIn("nodes", data)
        self.assertIn("edges", data)
        self.assertIn("is_mock", data)
        
        nodes = data["nodes"]
        if len(nodes) > 0:
            n = nodes[0]
            self.assertIn("id", n)
            self.assertIn("label", n)
            self.assertIn("group", n)


class TestBackendAgentRAG(unittest.TestCase):
    """Verify index creation and RAG querying capabilities."""
    
    def test_agent_query_rag(self):
        from core.agent import query
        # Querying information present in the indexed scenario PDF
        ans = query("Who is the CEO of INAYAT AI Solutions?")
        self.assertIsInstance(ans, str)
        self.assertGreater(len(ans), 0)
        
        # Verify the fallback system responds cleanly to generic questions
        fallback_ans = query("What is 5 + 5?")
        self.assertIn("10", fallback_ans)


class TestBackendHealth(unittest.TestCase):
    """Verify health monitor sweeps."""
    
    def test_health_monitor_sweep(self):
        from core.health import HealthMonitor
        monitor = HealthMonitor()
        status = monitor.run_all()
        self.assertEqual(status["gemini"], "🟢 Connected")
        self.assertEqual(status["mem0"], "🟢 Connected")
        self.assertEqual(status["neo4j"], "🟢 Connected")


if __name__ == "__main__":
    unittest.main()
