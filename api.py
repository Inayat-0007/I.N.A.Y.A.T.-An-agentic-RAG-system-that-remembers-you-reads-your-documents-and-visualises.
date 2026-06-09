# -*- coding: utf-8 -*-
"""I.N.A.Y.A.T. — FastAPI Backend Server.

Provides a unified REST API mapping all existing backend RAG functions,
profile memory pipelines, knowledge graph visualization, and resilience triggers.
Also serves the built React single page application.
"""

import os
import shutil
import logging
from typing import Optional, List, Dict, Any
import mimetypes

# Fail-safe MIME type mapping for Windows hosts serving ESM module files
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Core imports
from core.startup import run_startup
from core.health import HealthMonitor
from core.agent import query as agent_query, build_index, get_index
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
    monitor = HealthMonitor()
    statuses = monitor.run_all()
    
    # Check circuit breaker overrides
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
            "neo4j": is_graph_forced
        }
    }

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
    return {"status": "success", "service": req.service, "forced": req.forced}

@app.get("/api/memories")
def api_get_memories(user_id: str):
    """Fetch consolidated long-term memory facts for a user from Mem0."""
    if not user_id.strip():
        return {"memories": []}
    facts = get_memories(user_id)
    return {"memories": facts}

@app.post("/api/memories/clear")
def api_clear_memories(user_id: str):
    """Clear all Mem0 memory records for a given user profile."""
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="User ID is required")
    success = clear_memories(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear memories.")
    return {"status": "success"}

@app.get("/api/graph")
def api_get_graph(user_id: str):
    """Retrieve node-edge details for Vis.js representation."""
    if not user_id.strip():
        user_id = "default"
    # Pre-warm graph index
    get_index(user_id)
    data = get_visualization_data(user_id)
    return data

@app.post("/api/query")
def api_query_agent(req: QueryRequest):
    """Perform the 6-step prompt RAG reasoning query loop."""
    if not req.user_id.strip():
        raise HTTPException(status_code=400, detail="User ID is required")
        
    # Step 1: Add user interaction to Mem0 memory
    add_memory(req.user_id, req.question)
    
    # Step 2: Grab updated memory facts to form context
    mem_lines = get_memories(req.user_id)
    memory_ctx = "\n".join(f"• {m}" for m in mem_lines) if mem_lines else ""
    
    # Step 3 & 4: Run agent query engine (RAG + fallbacks)
    answer = agent_query(
        req.question,
        user_id=req.user_id,
        memory_context=memory_ctx
    )
    
    return {
        "answer": answer,
        "memory_context": memory_ctx,
        "memories": mem_lines
    }

@app.post("/api/upload")
async def api_upload_files(
    background_tasks: BackgroundTasks,
    user_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Ingest PDF/TXT documents into isolated profile folders and rebuild LlamaIndex."""
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="User ID is required")
        
    doc_dir = os.path.join("data", "documents", user_id)
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
         
    # Trigger synchronous indexing to match old app's wait-behavior
    # Visually blocking during indexing gives immediate feedback
    build_index(user_id)
    
    return {"status": "success", "indexed_files": saved_files}

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
