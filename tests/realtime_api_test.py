import json
import time
import threading
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import api


class TestRealtimeApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(api.app)
        with api._event_lock:
            api._event_log.clear()
            api._event_counter = 0
        with api._upload_jobs_lock:
            api._upload_jobs.clear()
        with api._user_state_lock:
            api._user_state.clear()

    @patch("api.agent_query", return_value="Hello from realtime stream.")
    @patch("api.get_memories", return_value=["enjoys graph rag"])
    @patch("api.add_memory", return_value=True)
    def test_query_stream_emits_tokens_and_final(self, _add_memory, _get_memories, _agent_query):
        with self.client.stream(
            "POST",
            "/api/query/stream",
            json={"question": "hello", "user_id": "rahul"},
        ) as response:
            self.assertEqual(response.status_code, 200)
            payloads = []
            for line in response.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                if not line.startswith("data: "):
                    continue
                payload = json.loads(line[6:])
                payloads.append(payload)
                if payload.get("type") == "final":
                    break

        self.assertTrue(any(p.get("type") == "token" for p in payloads))
        final = [p for p in payloads if p.get("type") == "final"][-1]
        self.assertEqual(final["answer"], "Hello from realtime stream.")
        self.assertEqual(final["memories"], ["enjoys graph rag"])

    @patch("api.build_index", return_value=object())
    def test_async_upload_job_status_endpoint(self, _build_index):
        files = [("files", ("sample.txt", b"hello", "text/plain"))]
        response = self.client.post("/api/upload", data={"user_id": "rahul"}, files=files)
        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body["status"], "accepted")
        job_id = body["job_id"]

        status = {}
        for _ in range(20):
            job_response = self.client.get(f"/api/upload/jobs/{job_id}")
            self.assertEqual(job_response.status_code, 200)
            status = job_response.json()
            if status.get("status") in {"completed", "failed"}:
                break
            time.sleep(0.05)

        self.assertIn(status.get("status"), {"completed", "failed"})
        self.assertEqual(status.get("user_id"), "rahul")

    def test_same_user_queries_are_serialized(self):
        with patch("api.add_memory", return_value=True), patch("api.get_memories", return_value=[]), patch(
            "api.agent_query", side_effect=lambda *args, **kwargs: (time.sleep(0.15), "ok")[1]
        ):
            start = time.perf_counter()
            errors = []
            done = []

            def run_query():
                try:
                    req = api.QueryRequest(question="hi", user_id="same-user")
                    result = api.api_query_agent(req)
                    done.append(result["answer"])
                except Exception as exc:
                    errors.append(exc)

            t1 = threading.Thread(target=run_query)
            t2 = threading.Thread(target=run_query)
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            elapsed = time.perf_counter() - start

        self.assertEqual(errors, [])
        self.assertEqual(done, ["ok", "ok"])
        self.assertGreaterEqual(elapsed, 0.28)

if __name__ == "__main__":
    unittest.main()
