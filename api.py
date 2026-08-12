# -*- coding: utf-8 -*-
"""I.N.A.Y.A.T. — FastAPI Backend Server.

HTTP adapter only: maps REST routes to ``core.*`` modules.
"""

import logging
import mimetypes
import os
from typing import List, Optional

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError

from core.agent import query_detailed
from core.conversation import append_turn
from core.exceptions import IndexBuildInProgress
from core.graph_store import get_visualization_data
from core.identity import InvalidUserId, UserId
from core.ingest import (
    build_index,
    get_index,
    get_index_status,
    save_uploads,
    schedule_index_build,
)
from core.memory import add_memory, clear_memories, get_memories
from core.observability import set_request_id
from core.schemas import QueryInput
from core.settings import get_settings
from core.startup import load_env, validate_env
from core.health import HealthMonitor
from core.resilience import DemoModeRequired, set_breaker_forced_open
import core.memory as mem
import core.graph_store as gs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inayat-api")

load_env()
_ok, _missing_crit, _missing_rec = validate_env()
_warnings = (
    [f"Missing recommended env vars: {', '.join(_missing_rec)}"] if _missing_rec else []
)
_health = {"gemini": "⚪ Unknown", "mem0": "⚪ Unknown", "neo4j": "⚪ Unknown"}

try:
    _settings = get_settings()
    _cors_origins = _settings.cors_origin_list
except ValidationError:
    _settings = None
    _cors_origins = ["http://localhost:5173", "http://localhost:8000"]

app = FastAPI(
    title="I.N.A.Y.A.T. API",
    description="Futuristic REST API layer for I.N.A.Y.A.T. RAG & Agentic Memory",
    version="2026.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str
    user_id: str
    memory_context: Optional[str] = ""


class ToggleBreakerRequest(BaseModel):
    service: str
    forced: bool


def _parse_user_id(raw: str) -> UserId:
    try:
        return UserId.parse(raw)
    except InvalidUserId as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/startup")
def api_startup():
    return {"ok": _ok, "health": _health, "warnings": _warnings}


@app.get("/api/health")
def api_health():
    monitor = HealthMonitor()
    statuses = monitor.run_all()
    is_mem_forced = getattr(mem._cb, "forced_open", False)
    is_graph_forced = getattr(gs._cb, "forced_open", False)
    return {
        "statuses": {
            "gemini": statuses.get("gemini", "⚪ Unknown"),
            "mem0": "🔴 Forced Fail" if is_mem_forced else statuses.get("mem0", "⚪ Unknown"),
            "neo4j": "🔴 Forced Fail"
            if is_graph_forced
            else statuses.get("neo4j", "⚪ Unknown"),
        },
        "breakers": {"mem0": is_mem_forced, "neo4j": is_graph_forced},
    }


@app.post("/api/health/toggle")
def api_toggle_breaker(req: ToggleBreakerRequest):
    try:
        if req.service == "mem0":
            set_breaker_forced_open(mem._cb, req.forced, service="Mem0")
        elif req.service == "neo4j":
            set_breaker_forced_open(gs._cb, req.forced, service="Neo4j")
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid service named. Use 'mem0' or 'neo4j'.",
            )
    except DemoModeRequired as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"status": "success", "service": req.service, "forced": req.forced}


@app.get("/api/memories")
def api_get_memories(user_id: str):
    if not user_id.strip():
        return {"memories": []}
    user = _parse_user_id(user_id)
    return {"memories": get_memories(user.value)}


@app.post("/api/memories/clear")
def api_clear_memories(user_id: str):
    user = _parse_user_id(user_id)
    success = clear_memories(user.value)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear memories.")
    return {"status": "success"}


@app.get("/api/graph")
def api_get_graph(user_id: str):
    user = _parse_user_id(user_id) if user_id.strip() else UserId.parse("default")
    get_index(user.value)
    return get_visualization_data(user.value)


@app.post("/api/query")
def api_query_agent(req: QueryRequest):
    _require_boot_ok()
    user = _parse_user_id(req.user_id)
    set_request_id(f"api-query-{user.value}")

    add_memory(user.value, req.question)
    mem_lines = get_memories(user.value)
    memory_ctx = "\n".join(f"• {m}" for m in mem_lines) if mem_lines else ""

    result = query_detailed(
        QueryInput(
            question=req.question,
            user_id=user.value,
            memory_context=memory_ctx,
        )
    )

    append_turn(user.value, "user", req.question)
    append_turn(user.value, "assistant", result.answer)

    return {
        "answer": result.answer,
        "route": result.route,
        "source_count": result.source_count,
        "used_memory": result.used_memory,
        "latency_ms": result.latency_ms,
        "memory_context": memory_ctx,
        "memories": mem_lines,
    }


def _require_boot_ok() -> None:
    if not _ok:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable: GEMINI_API_KEY is required to run queries and uploads.",
        )


@app.get("/api/index-status")
def api_index_status(user_id: str):
    user = _parse_user_id(user_id)
    return get_index_status(user.value)


@app.post("/api/upload")
async def api_upload_files(user_id: str = Form(...), files: List[UploadFile] = File(...)):
    _require_boot_ok()
    user = _parse_user_id(user_id)
    payloads = []
    for upload in files:
        if not upload.filename:
            continue
        payloads.append((upload.filename, await upload.read()))

    try:
        saved = save_uploads(user.value, payloads, overwrite=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not saved:
        raise HTTPException(status_code=400, detail="No valid PDF or TXT files were uploaded.")

    try:
        job_id = schedule_index_build(user.value)
    except IndexBuildInProgress as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(exc),
                "job_id": exc.job_id,
                "user_id": exc.user_id,
                "status": "building",
            },
        ) from exc

    return JSONResponse(
        status_code=202,
        content={
            "status": "accepted",
            "job_id": job_id,
            "indexed_files": saved,
            "index_status": get_index_status(user.value),
        },
    )


@app.post("/api/upload/sync")
async def api_upload_files_sync(
    user_id: str = Form(...), files: List[UploadFile] = File(...)
):
    """Synchronous upload + index (legacy compatibility)."""
    _require_boot_ok()
    user = _parse_user_id(user_id)
    payloads = []
    for upload in files:
        if not upload.filename:
            continue
        payloads.append((upload.filename, await upload.read()))

    try:
        saved = save_uploads(user.value, payloads, overwrite=True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not saved:
        raise HTTPException(status_code=400, detail="No valid PDF or TXT files were uploaded.")

    build_index(user.value)
    return {"status": "success", "indexed_files": saved, "index_status": get_index_status(user.value)}


frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
    logger.info("Serving built React SPA from /frontend/dist")
else:
    logger.warning("Vite production folder /frontend/dist not found.")

    @app.get("/")
    def read_root():
        return {
            "message": "FastAPI backend running. Start Vite dev server in /frontend/ for frontend development."
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
