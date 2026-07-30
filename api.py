# -*- coding: utf-8 -*-
"""I.N.A.Y.A.T. — FastAPI Backend Server.

Provides a unified REST API mapping all existing backend RAG functions,
profile memory pipelines, knowledge graph visualization, and resilience triggers.
Also serves the built React single page application.
"""

import os
import shutil
import time
import json
import uuid
import asyncio
import re
import threading
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Generator
import mimetypes

# Fail-safe MIME type mapping for Windows hosts serving ESM module files
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Core imports
from core.startup import run_startup
from core.health import HealthMonitor
from core.agent import query as agent_query, build_index, get_index, register_user_documents_dir
from core.memory import add_memory, get_memories, clear_memories
from core.graph_store import get_visualization_data
import core.memory as mem
import core.graph_store as gs

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inayat-api")

# Run environment check (Non-blocking file validation)
from core.startup import validate_env, load_env
load_env()
_ok, _missing_crit, _missing_rec = validate_env()
_warnings = [f"Missing recommended env vars: {', '.join(_missing_rec)}"] if _missing_rec else []
_health = {"gemini": "⚪ Unknown", "mem0": "⚪ Unknown", "neo4j": "⚪ Unknown"}

# Runtime state stores
_event_lock = threading.Lock()
_event_counter = 0
_event_log: List[Dict[str, Any]] = []
_event_log_max = 500

_user_lock_map: Dict[str, threading.Lock] = {}
_user_lock_map_lock = threading.Lock()
_user_state_lock = threading.Lock()
_user_state: Dict[str, Dict[str, bool]] = {}

_upload_jobs_lock = threading.Lock()
_upload_jobs: Dict[str, Dict[str, Any]] = {}

app = FastAPI(
    title="I.N.A.Y.A.T. API",
    description="Futuristic REST API layer for I.N.A.Y.A.T. RAG & Agentic Memory",
    version="2026.1.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API Data Models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str
    user_id: str
    memory_context: Optional[str] = ""

class ToggleBreakerRequest(BaseModel):
    service: str  # "mem0" or "neo4j"
    forced: bool


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_user_id(user_id: str) -> str:
    raw = (user_id or "default").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", raw):
        raise ValueError("Invalid user_id. Use only letters, numbers, _ or - (max 64 chars).")
    return raw


def _normalized_or_400(user_id: str) -> str:
    try:
        return _normalize_user_id(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _user_documents_dir(user_id: str) -> str:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "documents"))
    candidate = os.path.abspath(os.path.join(root, user_id))
    if not candidate.startswith(root + os.sep) and candidate != root:
        raise HTTPException(status_code=400, detail="Invalid user documents directory path.")
    return candidate


def _get_user_lock(user_id: str) -> threading.Lock:
    user_id = _normalize_user_id(user_id)
    with _user_lock_map_lock:
        if user_id not in _user_lock_map:
            _user_lock_map[user_id] = threading.Lock()
        return _user_lock_map[user_id]


@contextmanager
def _set_user_activity(user_id: str, activity: str):
    user_id = _normalize_user_id(user_id)
    with _user_state_lock:
        state = _user_state.setdefault(user_id, {"querying": False, "indexing": False})
        state[activity] = True
    try:
        yield
    finally:
        with _user_state_lock:
            state = _user_state.setdefault(user_id, {"querying": False, "indexing": False})
            state[activity] = False


def _snapshot_user_state(user_id: str) -> Dict[str, bool]:
    user_id = _normalize_user_id(user_id)
    with _user_state_lock:
        state = _user_state.get(user_id, {"querying": False, "indexing": False})
        return dict(state)


def _publish_event(event_type: str, payload: Dict[str, Any], user_id: Optional[str] = None) -> None:
    global _event_counter
    event = {
        "type": event_type,
        "payload": payload,
        "user_id": user_id,
        "created_at": _now_iso(),
    }
    with _event_lock:
        _event_counter += 1
        event["id"] = _event_counter
        _event_log.append(event)
        if len(_event_log) > _event_log_max:
            _event_log.pop(0)


def _fetch_events_since(last_id: int, user_id: str) -> List[Dict[str, Any]]:
    user_id = _normalize_user_id(user_id)
    with _event_lock:
        return [
            e
            for e in _event_log
            if e["id"] > last_id and (e["user_id"] is None or e["user_id"] == user_id)
        ]


def _get_health_snapshot() -> Dict[str, Any]:
    monitor = HealthMonitor()
    statuses = monitor.run_all()

    is_mem_forced = getattr(mem._cb, "forced_open", False)
    is_graph_forced = getattr(gs._cb, "forced_open", False)

    return {
        "statuses": {
            "gemini": statuses.get("gemini", "⚪ Unknown"),
            "mem0": "🔴 Forced Fail" if is_mem_forced else statuses.get("mem0", "⚪ Unknown"),
            "neo4j": "🔴 Forced Fail" if is_graph_forced else statuses.get("neo4j", "⚪ Unknown"),
        },
        "breakers": {
            "mem0": is_mem_forced,
            "neo4j": is_graph_forced,
        },
    }


def _chunk_answer(answer: str, chunk_size: int = 24) -> Generator[str, None, None]:
    if not answer:
        return
    for i in range(0, len(answer), chunk_size):
        yield answer[i : i + chunk_size]


def _upsert_job(job_id: str, **updates: Any) -> Dict[str, Any]:
    with _upload_jobs_lock:
        if job_id not in _upload_jobs:
            _upload_jobs[job_id] = {"job_id": job_id}
        _upload_jobs[job_id].update(updates)
        _upload_jobs[job_id]["updated_at"] = _now_iso()
        return dict(_upload_jobs[job_id])


def _get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _upload_jobs_lock:
        job = _upload_jobs.get(job_id)
        return dict(job) if job else None


def _latest_user_job(user_id: str) -> Optional[Dict[str, Any]]:
    user_id = _normalize_user_id(user_id)
    with _upload_jobs_lock:
        user_jobs = [j for j in _upload_jobs.values() if j.get("user_id") == user_id]
    if not user_jobs:
        return None
    return sorted(user_jobs, key=lambda j: j.get("updated_at", ""), reverse=True)[0]


def _run_index_job(job_id: str, user_id: str) -> None:
    user_id = _normalize_user_id(user_id)
    user_dir = _user_documents_dir(user_id)
    register_user_documents_dir(user_id, user_dir)
    running = _upsert_job(job_id, status="running")
    _publish_event("index_job_update", {"job": running}, user_id=user_id)
    try:
        with _get_user_lock(user_id), _set_user_activity(user_id, "indexing"):
            index = build_index(user_id)
        if index is None:
            finished = _upsert_job(job_id, status="failed", error="Index build returned no index.")
            _publish_event("index_job_update", {"job": finished}, user_id=user_id)
            _publish_event("index_error", {"job_id": job_id, "error": finished["error"]}, user_id=user_id)
            return

        finished = _upsert_job(job_id, status="completed", error=None)
        _publish_event("index_job_update", {"job": finished}, user_id=user_id)
        _publish_event("graph_updated", {"user_id": user_id, "reason": "index_completed"}, user_id=user_id)
    except Exception as exc:
        logger.error("Async indexing job failed for user %s: %s", user_id, exc, exc_info=True)
        failed = _upsert_job(job_id, status="failed", error=str(exc))
        _publish_event("index_job_update", {"job": failed}, user_id=user_id)
        _publish_event("index_error", {"job_id": job_id, "error": str(exc)}, user_id=user_id)

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/startup")
def api_startup():
    """Get initial bootstrap configurations and warning flags."""
    return {
        "ok": _ok,
        "health": _health,
        "warnings": _warnings
    }

@app.get("/api/health")
def api_health():
    """Retrieve full service health sweep & active circuit breaker statuses."""
    snapshot = _get_health_snapshot()
    _publish_event("health_update", snapshot, user_id=None)
    return snapshot

@app.post("/api/health/toggle")
def api_toggle_breaker(req: ToggleBreakerRequest):
    """Manually force open or close circuit breakers for resilience testing."""
    if req.service == "mem0":
        mem._cb.forced_open = req.forced
        logger.info(f"Mem0 circuit breaker forced_open set to {req.forced}")
    elif req.service == "neo4j":
        gs._cb.forced_open = req.forced
        logger.info(f"Neo4j circuit breaker forced_open set to {req.forced}")
    else:
        raise HTTPException(status_code=400, detail="Invalid service named. Use 'mem0' or 'neo4j'.")
    snapshot = _get_health_snapshot()
    _publish_event("health_update", snapshot, user_id=None)
    return {"status": "success", "service": req.service, "forced": req.forced}

@app.get("/api/memories")
def api_get_memories(user_id: str):
    """Fetch consolidated long-term memory facts for a user from Mem0."""
    if not user_id.strip():
        return {"memories": []}
    user_id = _normalized_or_400(user_id)
    facts = get_memories(user_id)
    return {"memories": facts}

@app.post("/api/memories/clear")
def api_clear_memories(user_id: str):
    """Clear all Mem0 memory records for a given user profile."""
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="User ID is required")
    user_id = _normalized_or_400(user_id)
    success = clear_memories(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear memories.")
    return {"status": "success"}

@app.get("/api/graph")
def api_get_graph(user_id: str):
    """Retrieve node-edge details for Vis.js representation."""
    if not user_id.strip():
        user_id = "default"
    user_id = _normalized_or_400(user_id)
    register_user_documents_dir(user_id, _user_documents_dir(user_id))
    # Pre-warm graph index with per-user lock
    with _get_user_lock(user_id):
        get_index(user_id)
    data = get_visualization_data(user_id)
    return data


@app.post("/api/index/warm")
def api_warm_index(user_id: str):
    """Warm a user's graph index cache in the background-safe path."""
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="User ID is required")
    user_id = _normalized_or_400(user_id)
    register_user_documents_dir(user_id, _user_documents_dir(user_id))
    with _get_user_lock(user_id):
        index = get_index(user_id)
    return {"status": "success", "warmed": index is not None}

@app.post("/api/query")
def api_query_agent(req: QueryRequest):
    """Perform the 6-step prompt RAG reasoning query loop."""
    if not req.user_id.strip():
        raise HTTPException(status_code=400, detail="User ID is required")
    user_id = _normalized_or_400(req.user_id)
    register_user_documents_dir(user_id, _user_documents_dir(user_id))
    with _get_user_lock(user_id), _set_user_activity(user_id, "querying"):
        add_memory(user_id, req.question)
        mem_lines = get_memories(user_id)
        memory_ctx = "\n".join(f"• {m}" for m in mem_lines) if mem_lines else ""
        answer = agent_query(
            req.question,
            user_id=user_id,
            memory_context=memory_ctx
        )
    _publish_event("memory_updated", {"memories": mem_lines}, user_id=user_id)
    _publish_event("graph_updated", {"user_id": user_id, "reason": "query"}, user_id=user_id)
    return {
        "answer": answer,
        "memory_context": memory_ctx,
        "memories": mem_lines
    }


@app.post("/api/query/stream")
def api_query_agent_stream(req: QueryRequest):
    """Stream query responses token-by-token for real-time chat rendering."""
    if not req.user_id.strip():
        raise HTTPException(status_code=400, detail="User ID is required")
    user_id = _normalized_or_400(req.user_id)
    register_user_documents_dir(user_id, _user_documents_dir(user_id))

    def _format(payload: Dict[str, Any]) -> str:
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    def _stream():
        try:
            with _get_user_lock(user_id), _set_user_activity(user_id, "querying"):
                add_memory(user_id, req.question)
                mem_lines = get_memories(user_id)
                memory_ctx = "\n".join(f"• {m}" for m in mem_lines) if mem_lines else ""
                answer = agent_query(
                    req.question,
                    user_id=user_id,
                    memory_context=memory_ctx
                )

            for chunk in _chunk_answer(answer):
                yield _format({"type": "token", "content": chunk})
                time.sleep(0.01)

            final_payload = {
                "type": "final",
                "answer": answer,
                "memories": mem_lines,
                "memory_context": memory_ctx,
            }
            yield _format(final_payload)
            _publish_event("memory_updated", {"memories": mem_lines}, user_id=user_id)
            _publish_event("graph_updated", {"user_id": user_id, "reason": "query"}, user_id=user_id)
        except Exception as exc:
            logger.error("Streaming query failed for user %s: %s", user_id, exc, exc_info=True)
            message = "I'm sorry, I'm having trouble connecting to my services right now. Please try again in a moment."
            yield _format({"type": "error", "error": message})
            _publish_event("query_error", {"error": str(exc)}, user_id=user_id)

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    return StreamingResponse(_stream(), media_type="text/event-stream", headers=headers)

@app.post("/api/upload")
async def api_upload_files(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Ingest PDF/TXT documents into isolated profile folders and rebuild LlamaIndex."""
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="User ID is required")
    user_id = _normalized_or_400(user_id)
    doc_dir = _user_documents_dir(user_id)
    register_user_documents_dir(user_id, doc_dir)
    os.makedirs(doc_dir, exist_ok=True)
    
    saved_files = []
    for file in files:
        if not file.filename.lower().endswith((".pdf", ".txt")):
            continue
        file_path = os.path.join(doc_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
        
    if not saved_files:
         raise HTTPException(status_code=400, detail="No valid PDF or TXT files were uploaded.")
         
    job_id = str(uuid.uuid4())
    job = _upsert_job(
        job_id,
        user_id=user_id,
        status="pending",
        error=None,
        indexed_files=saved_files,
        created_at=_now_iso(),
    )
    _publish_event("index_job_update", {"job": job}, user_id=user_id)
    background_tasks.add_task(_run_index_job, job_id, user_id)

    return {"status": "accepted", "job_id": job_id, "indexed_files": saved_files}


@app.get("/api/upload/jobs/{job_id}")
def api_upload_job_status(job_id: str):
    """Return upload/indexing job status by id."""
    job = _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/events")
async def api_events(user_id: str):
    """SSE stream for live health, indexing, memory, and graph updates."""
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="User ID is required")
    user_id = _normalized_or_400(user_id)

    async def _events():
        init_payload = {
            "type": "init",
            "payload": {
                "health": _get_health_snapshot(),
                "user_state": _snapshot_user_state(user_id),
                "active_job": _latest_user_job(user_id),
            },
        }
        yield f"data: {json.dumps(init_payload, ensure_ascii=False)}\n\n"

        last_id = 0
        while True:
            events = _fetch_events_since(last_id, user_id)
            if events:
                for event in events:
                    last_id = max(last_id, event["id"])
                    payload = {
                        "type": event["type"],
                        "payload": event["payload"],
                        "created_at": event["created_at"],
                    }
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            else:
                yield ": keepalive\n\n"
            await asyncio.sleep(1.0)

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    return StreamingResponse(_events(), media_type="text/event-stream", headers=headers)

# ---------------------------------------------------------------------------
# SPA Static Hosting
# ---------------------------------------------------------------------------
# Locate built frontend folder
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(frontend_dist):
    # Mount production React build
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
    logger.info("Serving built React SPA from /frontend/dist")
else:
    logger.warning("Vite production folder /frontend/dist not found. Please compile frontend first.")
    # Expose a placeholder root index during local development
    @app.get("/")
    def read_root():
        return {
            "message": "FastAPI backend running. Start Vite dev server in /frontend/ for frontend development."
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
