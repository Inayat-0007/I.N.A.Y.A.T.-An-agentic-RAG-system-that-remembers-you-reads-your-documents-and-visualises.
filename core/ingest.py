"""Document filesystem persistence and PropertyGraphIndex lifecycle.

Writes uploaded files to per-user folders and builds LlamaIndex indices.
This module must not answer user questions or serve HTTP/UI.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Dict, Iterable, List, Literal, Optional, Sequence, Tuple, Union

from llama_index.core import Document, PropertyGraphIndex
from llama_index.core.indices.property_graph import ImplicitPathExtractor

from core.exceptions import IndexBuildInProgress
from core.graph_store import (
    delete_user_chunks,
    get_neo4j_property_graph_store,
    stamp_chunks_for_user,
)
from core.identity import UserId
from core.llm_setup import configure_llama_settings
from core.observability import trace_span
from core.settings import get_settings

logger = logging.getLogger("inayat")

_DOC_ROOT = Path(__file__).resolve().parent.parent / "data" / "documents"
_MANIFEST_NAME = ".indexed.json"
_INDEXABLE_SUFFIXES = {".pdf", ".txt"}
# from_documents/insert can hang on Gemini embed or a shared Aura graph.
_BUILD_TIMEOUT_SEC = 300.0

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


def _indexable_files(user_dir: Path) -> List[Path]:
    if not user_dir.is_dir():
        return []
    return sorted(
        f
        for f in user_dir.iterdir()
        if f.is_file()
        and not f.name.startswith(".")
        and f.suffix.lower() in _INDEXABLE_SUFFIXES
    )


def _file_fingerprint(path: Path) -> Dict[str, int]:
    stat = path.stat()
    return {"size": int(stat.st_size), "mtime_ns": int(stat.st_mtime_ns)}


def _load_manifest(user_dir: Path) -> Dict[str, Dict[str, int]]:
    path = user_dir / _MANIFEST_NAME
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        files = payload.get("files") if isinstance(payload, dict) else None
        return files if isinstance(files, dict) else {}
    except Exception as exc:
        logger.warning("Could not read ingest manifest %s: %s", path, exc)
        return {}


def _write_manifest(user_dir: Path, files: Dict[str, Dict[str, int]]) -> None:
    path = user_dir / _MANIFEST_NAME
    path.write_text(
        json.dumps({"files": files}, indent=2),
        encoding="utf-8",
    )


def _pending_files(
    user_dir: Path, only_files: Optional[Sequence[str]] = None
) -> Tuple[List[Path], List[Path]]:
    """Return (to_index, skipped) based on the on-disk manifest."""
    all_files = _indexable_files(user_dir)
    if only_files:
        wanted = {Path(name).name for name in only_files}
        all_files = [f for f in all_files if f.name in wanted]
    known = _load_manifest(user_dir)
    pending: List[Path] = []
    skipped: List[Path] = []
    for path in all_files:
        if known.get(path.name) == _file_fingerprint(path):
            skipped.append(path)
        else:
            pending.append(path)
    return pending, skipped


def _extract_pdf_text(path: Path) -> str:
    """Extract real text from a PDF. Never index raw ``%PDF`` bytes."""
    text = ""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception as exc:
        logger.warning("pypdf failed for %s: %s", path.name, exc)

    if not text or text.lstrip().startswith("%PDF"):
        try:
            import fitz

            with fitz.open(str(path)) as doc:
                text = "\n".join(page.get_text() for page in doc).strip()
        except Exception as exc:
            logger.warning("PyMuPDF failed for %s: %s", path.name, exc)

    if not text or text.lstrip().startswith("%PDF"):
        raise ValueError(
            f"Could not extract text from PDF '{path.name}'. "
            "Install pypdf/pymupdf in the runtime image, or use a text PDF "
            "(scanned/image-only files are not supported)."
        )
    return text


def _load_documents(paths: List[Path], uid: str) -> List[Document]:
    """Load PDF/TXT files as LlamaIndex documents with ``user_id`` metadata."""
    docs: List[Document] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            text = _extract_pdf_text(path)
        elif suffix == ".txt":
            text = path.read_text(encoding="utf-8")
        else:
            continue
        docs.append(
            Document(
                text=text,
                metadata={
                    "user_id": uid,
                    "file_name": path.name,
                    "file_path": str(path.resolve()),
                    "file_type": suffix,
                },
            )
        )
    return docs


def _kg_extractors() -> list:
    """Skip per-chunk LLM triplet extraction (the main ingest bottleneck).

    Chunk embeddings still run, so RAG retrieval keeps working. Graph edges
    come from implicit prev/next/source links instead of Gemini KG calls.
    """
    return [ImplicitPathExtractor()]


def _has_documents(user_id: str) -> bool:
    user_dir = _DOC_ROOT / user_id
    return len(_indexable_files(user_dir)) > 0


def user_has_documents(user_id: str) -> bool:
    """Return True when the user folder contains indexable files."""
    uid = UserId.parse(user_id).value
    return _has_documents(uid)


def list_user_documents(user_id: str) -> List[dict]:
    """Return on-disk PDF/TXT files for the sidebar (name, size, mtime)."""
    uid = UserId.parse(user_id).value
    user_dir = document_dir_for(UserId.parse(uid))
    rows: List[dict] = []
    for path in _indexable_files(user_dir):
        stat = path.stat()
        rows.append(
            {
                "name": path.name,
                "size": int(stat.st_size),
                "mtime": stat.st_mtime,
            }
        )
    return rows


def unindexed_document_names(user_id: str) -> List[str]:
    """Return filenames on disk that are missing from the ingest manifest."""
    uid = UserId.parse(user_id).value
    user_dir = document_dir_for(UserId.parse(uid))
    pending, _skipped = _pending_files(user_dir)
    return [path.name for path in pending]


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

            if safe_name.lower().endswith(".pdf") and not payload.startswith(b"%PDF"):
                raise ValueError(
                    f"File '{safe_name}' is not a valid PDF (missing %PDF header)."
                )
            if safe_name.lower().endswith(".txt"):
                try:
                    payload.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ValueError(
                        f"File '{safe_name}' is not valid UTF-8 text."
                    ) from exc

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


def _load_existing_index(graph_store) -> PropertyGraphIndex:
    return PropertyGraphIndex.from_existing(
        property_graph_store=graph_store,
        kg_extractors=_kg_extractors(),
        use_async=False,
        show_progress=False,
    )


def _run_with_timeout(fn, timeout_sec: float):
    """Wait for ``fn`` up to ``timeout_sec``; do not block the UI forever."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn)
        try:
            return future.result(timeout=timeout_sec)
        except concurrent.futures.TimeoutError as exc:
            logger.error(
                "Index build exceeded %.0fs — stopping wait (worker may still run).",
                timeout_sec,
            )
            raise TimeoutError(
                f"Indexing timed out after {int(timeout_sec)}s. "
                "Retry after refresh, or restart the app if it stays stuck."
            ) from exc


def _index_documents(
    docs,
    graph_store,
    existing: Optional[PropertyGraphIndex],
) -> PropertyGraphIndex:
    extractors = _kg_extractors()
    if existing is not None:
        logger.info(
            "Incrementally inserting %d document(s) into this user's cached index.",
            len(docs),
        )

        def _insert_all():
            for i, doc in enumerate(docs, 1):
                started = time.time()
                preview = (doc.text or "")[:80].replace("\n", " ")
                logger.info(
                    "Insert %d/%d (%d chars) starting: %s",
                    i,
                    len(docs),
                    len(doc.text or ""),
                    preview,
                )
                existing.insert(doc)
                logger.info(
                    "Insert %d/%d finished in %.1fs",
                    i,
                    len(docs),
                    time.time() - started,
                )
            return existing

        return _run_with_timeout(_insert_all, _BUILD_TIMEOUT_SEC)
    logger.info("Building PropertyGraphIndex from %d new document(s).", len(docs))
    return _run_with_timeout(
        lambda: PropertyGraphIndex.from_documents(
            docs,
            property_graph_store=graph_store,
            kg_extractors=extractors,
            use_async=False,
            show_progress=True,
        ),
        _BUILD_TIMEOUT_SEC,
    )


def _execute_index_build(
    uid: str,
    only_files: Optional[Sequence[str]] = None,
    *,
    force: bool = False,
) -> Optional[PropertyGraphIndex]:
    """Build or incrementally update index (caller must hold per-user lock)."""
    settings = get_settings()
    configure_llama_settings(settings)
    graph_store = get_neo4j_property_graph_store()
    if graph_store is None:
        logger.warning("Neo4j graph store unavailable — cannot build index.")
        return None

    user = UserId.parse(uid)
    user_dir = document_dir_for(user)

    if force:
        delete_user_chunks(uid)
        _write_manifest(user_dir, {})
        logger.info("Force reindex: cleared chunks and manifest for %s", uid)

    if not _has_documents(uid):
        if not settings.allow_empty_from_existing:
            logger.info("No documents for %s and from_existing disabled.", user_dir)
            return None
        logger.info("No documents in %s — loading existing graph index.", user_dir)
        try:
            index = _load_existing_index(graph_store)
            _indices[uid] = index
            return index
        except Exception as exc:
            logger.error("Failed to load existing index: %s", exc)
            return None

    pending, skipped = _pending_files(user_dir, only_files=only_files)
    logger.info(
        "Ingest plan for %s: %d new/changed, %d already indexed%s",
        uid,
        len(pending),
        len(skipped),
        f" (only_files={list(only_files)})" if only_files else "",
    )

    if not pending:
        cached = _indices.get(uid)
        if cached is not None:
            logger.info("Index already up to date for user %s — skipping rebuild.", uid)
            _write_manifest(
                user_dir,
                {p.name: _file_fingerprint(p) for p in _indexable_files(user_dir)},
            )
            return cached
        try:
            index = _run_with_timeout(
                lambda: _load_existing_index(graph_store),
                min(_BUILD_TIMEOUT_SEC, 45.0),
            )
            _indices[uid] = index
            _write_manifest(
                user_dir,
                {p.name: _file_fingerprint(p) for p in _indexable_files(user_dir)},
            )
            logger.info("Loaded existing graph index for user %s (no new files).", uid)
            return index
        except Exception as exc:
            logger.warning("from_existing failed for %s: %s — rebuilding.", uid, exc)
            pending = _indexable_files(user_dir)

    try:
        # Only incrementally insert into THIS user's in-memory index.
        # Attaching the shared Aura graph via from_existing hydrates other
        # profiles' nodes; insert() then hangs on Gemini KG/embed.
        existing = _indices.get(uid)
        if existing is None and pending:
            logger.info(
                "No in-memory index for %s — building from pending files only "
                "(not attaching shared Neo4j from_existing).",
                uid,
            )

        if pending:
            docs = _load_documents(pending, uid)
            logger.info(
                "Loaded %d chunks from %d new file(s) for user %s: %s",
                len(docs),
                len(pending),
                uid,
                [p.name for p in pending],
            )
            index = _index_documents(docs, graph_store, existing)
            stamp_chunks_for_user(uid, [p.name for p in pending])
        else:
            docs = _load_documents(_indexable_files(user_dir), uid)
            logger.info(
                "Loaded %d document chunks for user %s from %s",
                len(docs),
                uid,
                user_dir,
            )
            index = _index_documents(docs, graph_store, None)
            stamp_chunks_for_user(uid, [p.name for p in _indexable_files(user_dir)])

        current = {p.name: _file_fingerprint(p) for p in _indexable_files(user_dir)}
        _write_manifest(user_dir, current)
        logger.info("PropertyGraphIndex updated successfully for user %s.", uid)
        _indices[uid] = index
        return index
    except Exception as exc:
        logger.error("Index build failed: %s", exc, exc_info=True)
        raise


def build_index(
    user_id: str = "default",
    only_files: Optional[Sequence[str]] = None,
    *,
    force: bool = False,
) -> Optional[PropertyGraphIndex]:
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
                result = _execute_index_build(
                    uid, only_files=only_files, force=force
                )
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


def schedule_index_build(
    user_id: str, only_files: Optional[Sequence[str]] = None
) -> str:
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
                result = _execute_index_build(uid, only_files=only_files)
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

    if not _has_documents(uid) and not get_settings().allow_empty_from_existing:
        logger.info(
            "No documents for %s and INAYAT_ALLOW_EMPTY_FROM_EXISTING=false — "
            "skipping from_existing (LLM fallback will be explicit).",
            uid,
        )
        return None

    with _indices_lock:
        cached = _indices.get(uid)
        if cached is not None:
            return cached
        try:
            return build_index(uid)
        except Exception:
            logger.exception("Synchronous index build failed for %s", uid)
            return None
