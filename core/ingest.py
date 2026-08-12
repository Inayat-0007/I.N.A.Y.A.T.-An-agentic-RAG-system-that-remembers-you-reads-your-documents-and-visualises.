"""Document filesystem persistence and PropertyGraphIndex lifecycle.

Writes uploaded files to per-user folders and builds LlamaIndex indices.
This module must not answer user questions or serve HTTP/UI.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, List, Literal, Optional, Tuple, Union

from llama_index.core import PropertyGraphIndex, SimpleDirectoryReader

from core.exceptions import IndexBuildInProgress
from core.graph_store import get_neo4j_property_graph_store
from core.identity import UserId
from core.llm_setup import configure_llama_settings
from core.observability import trace_span
from core.settings import get_settings

logger = logging.getLogger("inayat")

_DOC_ROOT = Path(__file__).resolve().parent.parent / "data" / "documents"

_indices: dict[str, PropertyGraphIndex] = {}
_indices_lock = threading.Lock()
_user_build_locks: dict[str, threading.Lock] = {}
_user_build_locks_guard = threading.Lock()

IndexStatus = Literal["idle", "building", "ready", "error"]


@dataclass
class _IndexJob:
    status: IndexStatus
    job_id: str
    error: Optional[str] = None
    updated_at: float = 0.0


_index_jobs: dict[str, _IndexJob] = {}
_jobs_lock = threading.Lock()


def document_root() -> Path:
    """Return the root directory for per-user document storage."""
    return _DOC_ROOT


def document_dir_for(user: UserId) -> Path:
    """Return (and create) the document directory for a validated user."""
    path = _DOC_ROOT / user.value
    path.mkdir(parents=True, exist_ok=True)
    return path


def _user_lock(user_id: str) -> threading.Lock:
    with _user_build_locks_guard:
        if user_id not in _user_build_locks:
            _user_build_locks[user_id] = threading.Lock()
        return _user_build_locks[user_id]


def _has_documents(user_id: str) -> bool:
    user_dir = _DOC_ROOT / user_id
    if not user_dir.is_dir():
        return False
    files = [f for f in user_dir.iterdir() if f.is_file() and not f.name.startswith(".")]
    return len(files) > 0


def get_index_status(user_id: str) -> dict:
    """Return the current index build status for a user."""
    uid = UserId.parse(user_id).value
    with _jobs_lock:
        job = _index_jobs.get(uid)
        if job is None:
            return {
                "user_id": uid,
                "status": "idle",
                "job_id": None,
                "error": None,
                "updated_at": None,
            }
        return {
            "user_id": uid,
            "status": job.status,
            "job_id": job.job_id,
            "error": job.error,
            "updated_at": job.updated_at,
        }


def save_uploads(
    user_id: str,
    files: Iterable[Tuple[str, Union[bytes, BinaryIO]]],
    *,
    overwrite: bool = True,
) -> List[str]:
    """Persist uploaded documents for a user.

    Raises:
        InvalidUserId: When ``user_id`` fails validation.
        ValueError: When a file exceeds ``max_upload_bytes`` or has invalid type.
    """
    user = UserId.parse(user_id)
    settings = get_settings()
    user_dir = document_dir_for(user)
    saved: List[str] = []

    with trace_span("ingest.save_uploads", user_id=user.value):
        for filename, content in files:
            safe_name = Path(filename).name
            if not safe_name or safe_name.startswith("."):
                continue
            if not safe_name.lower().endswith((".pdf", ".txt")):
                continue

            if isinstance(content, (bytes, bytearray)):
                payload = bytes(content)
            else:
                payload = content.read()

            if len(payload) > settings.max_upload_bytes:
                raise ValueError(
                    f"File '{safe_name}' exceeds maximum upload size "
                    f"({settings.max_upload_bytes} bytes)."
                )

            target = user_dir / safe_name
            if target.exists() and not overwrite:
                continue

            target.write_bytes(payload)
            saved.append(safe_name)
            logger.info("Saved upload %s for user %s", safe_name, user.value)

    return saved


def _execute_index_build(uid: str) -> Optional[PropertyGraphIndex]:
    """Build index for user (caller must hold per-user lock)."""
    settings = get_settings()
    configure_llama_settings(settings)
    graph_store = get_neo4j_property_graph_store()
    if graph_store is None:
        logger.warning("Neo4j graph store unavailable — cannot build index.")
        return None

    user = UserId.parse(uid)
    user_dir = document_dir_for(user)

    if not _has_documents(uid):
        if not settings.allow_empty_from_existing:
            logger.info("No documents for %s and from_existing disabled.", user_dir)
            return None
        logger.info("No documents in %s — loading existing graph index.", user_dir)
        try:
            index = PropertyGraphIndex.from_existing(property_graph_store=graph_store)
            _indices[uid] = index
            return index
        except Exception as exc:
            logger.error("Failed to load existing index: %s", exc)
            return None

    try:
        reader = SimpleDirectoryReader(str(user_dir))
        docs = reader.load_data()
        for doc in docs:
            doc.metadata["user_id"] = uid

        logger.info(
            "Loaded %d document chunks for user %s from %s",
            len(docs),
            uid,
            user_dir,
        )

        index = PropertyGraphIndex.from_documents(
            docs,
            property_graph_store=graph_store,
            show_progress=True,
        )
        logger.info("PropertyGraphIndex built successfully for user %s.", uid)
        _indices[uid] = index
        return index
    except Exception as exc:
        logger.error("Index build failed: %s", exc, exc_info=True)
        return None


def build_index(user_id: str = "default") -> Optional[PropertyGraphIndex]:
    """Synchronously build index (blocks until complete; used by Streamlit)."""
    user = UserId.parse(user_id)
    uid = user.value

    with trace_span("ingest.build_index", user_id=uid, mode="sync"):
        with _jobs_lock:
            _index_jobs[uid] = _IndexJob(
                status="building",
                job_id=str(uuid.uuid4()),
                updated_at=time.time(),
            )
        try:
            with _user_lock(uid):
                result = _execute_index_build(uid)
            with _jobs_lock:
                _index_jobs[uid] = _IndexJob(
                    status="ready" if result is not None else "error",
                    job_id=_index_jobs[uid].job_id,
                    error=None if result is not None else "Index build returned no index.",
                    updated_at=time.time(),
                )
            return result
        except Exception as exc:
            with _jobs_lock:
                _index_jobs[uid] = _IndexJob(
                    status="error",
                    job_id=_index_jobs[uid].job_id,
                    error=str(exc),
                    updated_at=time.time(),
                )
            raise


def schedule_index_build(user_id: str) -> str:
    """Start background index build; returns job id.

    Raises:
        IndexBuildInProgress: When a build is already running for this user.
    """
    uid = UserId.parse(user_id).value

    with _jobs_lock:
        existing = _index_jobs.get(uid)
        if existing and existing.status == "building":
            raise IndexBuildInProgress(existing.job_id, uid)
        job_id = str(uuid.uuid4())
        _index_jobs[uid] = _IndexJob(
            status="building", job_id=job_id, updated_at=time.time()
        )

    def _worker() -> None:
        try:
            with _user_lock(uid):
                result = _execute_index_build(uid)
            with _jobs_lock:
                _index_jobs[uid] = _IndexJob(
                    status="ready" if result is not None else "error",
                    job_id=job_id,
                    error=None if result is not None else "Index build returned no index.",
                    updated_at=time.time(),
                )
        except Exception as exc:
            logger.error("Background index build failed for %s: %s", uid, exc)
            with _jobs_lock:
                _index_jobs[uid] = _IndexJob(
                    status="error",
                    job_id=job_id,
                    error=str(exc),
                    updated_at=time.time(),
                )

    threading.Thread(
        target=_worker, name=f"inayat-index-{uid}", daemon=True
    ).start()
    return job_id


def get_index(user_id: str = "default") -> Optional[PropertyGraphIndex]:
    """Return cached index for user, building synchronously on first call."""
    user = UserId.parse(user_id)
    uid = user.value

    cached = _indices.get(uid)
    if cached is not None:
        return cached

    with _indices_lock:
        cached = _indices.get(uid)
        if cached is not None:
            return cached
        return build_index(uid)
