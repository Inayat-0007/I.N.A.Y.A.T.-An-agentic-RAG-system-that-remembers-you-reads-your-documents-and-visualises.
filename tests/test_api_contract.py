"""FastAPI contract tests (HOW_TO_FIX §9.4). Loaded by smoke_test __main__."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("GEMINI_API_KEY", "test-api-contract-key")

from core.startup import load_env

load_env()


class TestApiContract(unittest.TestCase):
    """HTTP contract checks without live external services."""

    @classmethod
    def setUpClass(cls) -> None:
        from fastapi.testclient import TestClient

        from api import app

        cls.client = TestClient(app)

    def setUp(self) -> None:
        os.environ["GEMINI_API_KEY"] = "test-api-contract-key"
        os.environ["INAYAT_DEMO_MODE"] = "false"
        os.environ.pop("INAYAT_API_KEY", None)
        from core.settings import clear_settings_cache

        clear_settings_cache()

    def test_invalid_user_id_returns_400(self) -> None:
        res = self.client.post(
            "/api/query",
            json={"question": "hello", "user_id": "../etc"},
        )
        self.assertEqual(res.status_code, 400)

    def test_toggle_breaker_without_demo_mode_returns_403(self) -> None:
        res = self.client.post(
            "/api/health/toggle",
            json={"service": "mem0", "forced": True},
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("INAYAT_DEMO_MODE", res.json().get("detail", ""))

    def test_cors_disallowed_origin_not_reflected(self) -> None:
        res = self.client.get(
            "/api/health",
            headers={"Origin": "https://evil.example.com"},
        )
        self.assertEqual(res.status_code, 200)
        allow_origin = res.headers.get("access-control-allow-origin")
        self.assertNotEqual(allow_origin, "https://evil.example.com")

    def test_request_id_header_present(self) -> None:
        res = self.client.get("/api/health")
        self.assertIn("x-request-id", res.headers)


if __name__ == "__main__":
    unittest.main()
