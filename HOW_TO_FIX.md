# HOW TO FIX — I.N.A.Y.A.T. Remediation Architecture

> **Remediation spec (not runtime truth):** Instructions below reference outdated values only where describing fixes. Current status: [README.md](README.md), [STATUS.md](STATUS.md).
>
> **Implementation:** `HOW_TO_FIX.md` §1–§13 is **complete** as of 2026-08-13 (order in §10; no LangGraph). Smoke: `python tests/smoke_test.py` (52 tests).

**Companion to:** `WHAT_TO_FIX.md`  
**Constraint:** Backwards compatible. Do not rip out Streamlit, Mem0, Neo4j, or the existing `query()` contract until a migration path is live.  
**Python target (single source of truth):** **3.12** — already used by Docker; CI and docs must follow.  
**Default product surface (target):** FastAPI + React SPA. Streamlit remains a supported legacy entry until Docker CMD is switched.

This document is the implementation specification. Every item in `WHAT_TO_FIX.md` section D maps to a module, interface, failure mode, and verification step below. No placeholders. No “rest of code here.”

---

## 0. Architectural Decision Matrix

### 0.1 Component boundaries (strict SRP)

| Component               | One job                                  | Public interface                                                                   | Must not do                     |
| ----------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------- |
| `core/settings.py`      | Load and validate env                    | `get_settings() -> InayatSettings`                                                 | Call Gemini/Neo4j/Mem0          |
| `core/identity.py`      | Sanitize and type `user_id`              | `UserId.parse(raw: str) -> UserId`                                                 | Persist files or query DBs      |
| `core/observability.py` | Correlate logs + timings                 | `trace_span(name, **attrs)`                                                        | Business logic                  |
| `core/llm_setup.py`     | LLM + embeddings only                    | `get_gemini_llm()`, `get_gemini_embedding()`, `configure_llama_settings(settings)` | Index documents                 |
| `core/ingest.py`        | Filesystem write + index build           | `save_uploads()`, `build_index(user_id)`                                           | Answer questions                |
| `core/agent.py`         | Retrieve + generate answer               | `query(QueryInput) -> QueryResult`                                                 | Serve HTTP or Streamlit widgets |
| `core/memory.py`        | Long-term Mem0 only                      | `add_memory`, `get_memories`, `search_memories`, `clear_memories`                  | Hold chat transcripts           |
| `core/conversation.py`  | Short-term buffer (optional server-side) | `append_turn`, `recent_turns`                                                      | Call Mem0                       |
| `core/graph_store.py`   | Neo4j driver + vis payload               | `run_cypher`, `get_visualization_data`                                             | Call Gemini                     |
| `core/resilience.py`    | Breaker + retry + safe_execute           | existing API + per-service instances                                               | Know about users                |
| `core/health.py`        | Probe externals                          | `HealthMonitor.run_all()`                                                          | Mutate breakers                 |
| `api.py`                | HTTP + auth + static SPA                 | REST contracts                                                                     | Embed LlamaIndex internals      |
| `app.py`                | Streamlit adapter                        | Calls `core.*` only                                                                | Duplicate RAG logic             |
| `frontend/`             | Presentation                             | Typed fetch wrappers                                                               | Invent RAG/memory truth         |

### 0.2 Failure design (up front)

| Failure                           | Bottleneck           | Default                                                       | User-visible result                                   |
| --------------------------------- | -------------------- | ------------------------------------------------------------- | ----------------------------------------------------- |
| Missing `GEMINI_API_KEY`          | Boot                 | Refuse start                                                  | Clear error, process exit 1                           |
| Gemini timeout / 429              | Network              | 6× exponential backoff then fallback string                   | Apology or last-good LLM text                         |
| Neo4j down                        | Network / Aura sleep | Circuit OPEN after 3 fails                                    | RAG skipped; Gemini-only answer; vis `is_mock`        |
| Mem0 down                         | Network              | Circuit OPEN after 3 fails                                    | Empty memories; answer still produced                 |
| Upload of 50 MB PDF               | Memory / CPU         | Reject > configured max bytes; index in background thread     | `202 Accepted` + job id (API); Streamlit spinner kept |
| Concurrent index builds same user | Concurrency          | Per-user lock (already `_indices_lock`; extend to per-user)   | Second request waits or returns `409 indexing`        |
| Path-traversal `user_id`          | Input                | Reject at `UserId.parse`                                      | HTTP 400 / Streamlit error                            |
| Cross-user graph hop leak         | Data model           | Vis Cypher constrained to `user_id` on **all** returned nodes | No unlabeled Entity without user tag                  |
| Forced breaker toggle             | Demo                 | Keep `forced_open` but require `INAYAT_DEMO_MODE=true`        | 403 if demo mode off                                  |
| Dual UI drift                     | Product              | Shared `QueryResult` schema                                   | Both UIs consume same fields                          |

### 0.3 Backwards compatibility rules

1. Keep `core.agent.query(question, user_id="default", memory_context="") -> str` as a thin wrapper around the new typed `query()` so Streamlit and existing tests do not break.
2. Keep Streamlit `app.py` runnable until Docker CMD changes in a dedicated release note.
3. Keep Mem0 `user_id` string semantics; only **validate** the string, do not rename tenants.
4. Keep circuit breaker `forced_open` for the demo script; gate it with env.
5. Do not require pytest for CI smoke; keep `python tests/smoke_test.py`. Add pytest later as additive.

---

## 1. P0 — Single trustworthy status (docs + truth)

### 1.1 Canonical facts (copy these into README; delete contradictions)

| Fact            | Canonical value                                                                                            |
| --------------- | ---------------------------------------------------------------------------------------------------------- |
| Maturity        | Advanced MVP / demo-ready; not hardened production                                                         |
| Agent model     | **Single-agent RAG pipeline** (not LangGraph/CrewAI multi-agent)                                           |
| Python          | **3.12**                                                                                                   |
| LLM             | `gemini-flash-lite-latest`                                                                                 |
| Embeddings      | `gemini-embedding-001` (3072-dim)                                                                          |
| Chunking        | size 512, overlap 64 (env-overridable after §3)                                                            |
| Retrieval       | PropertyGraphIndex, `similarity_top_k=5`, `user_id` metadata filter                                        |
| Tests           | **21** smoke (`tests/smoke_test.py`) + **10** live integration (`tests/backend_feature_test.py`) = **31**  |
| CI              | flake8 (E9,F63,F7,F82) + black + gitleaks + smoke tests; **does not** run backend_feature_test on every PR |
| Docker          | `python:3.12-slim`, Streamlit `:8501` **today**; compose is **one** service                                |
| Seed docs       | **None in git** — only `data/documents/.gitkeep`                                                           |
| UIs             | Streamlit (`app.py`) **and** FastAPI+React (`api.py`, `frontend/`)                                         |
| Isolation       | Soft: folder + metadata + Mem0 `user_id`; **shared Neo4j DB**; **no auth**                                 |
| Critical env    | `GEMINI_API_KEY` only                                                                                      |
| Recommended env | `MEM0_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`                                            |

### 1.2 File roles after cleanup

| File                          | Role                                                                                                        |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `README.md`                   | Install, run, architecture diagram, **canonical facts table**                                               |
| `CONTEXT.md`                  | Contributor map of modules (must match tree)                                                                |
| `MASTER_DEEP_DIVE_REPORT.txt` | Historical snapshot **or** add a banner: “Superseded by README canonical facts; do not use for test counts” |
| `WHAT_TO_FIX.md`              | Issue inventory (this work)                                                                                 |
| `HOW_TO_FIX.md`               | This spec                                                                                                   |
| `STATUS.md`                   | One-page examiner sheet generated from the canonical table                                                  |

### 1.3 README edits (exact)

- Badge Python: `3.12` not `3.14`
- Badge tests: `21 smoke / 10 live / CI=smoke` not `19/19`
- Tech table: Gemini Flash Lite latest, not Gemini 1.5 Flash
- Dependency versions: quote `constraints.txt` pins
- Tree: include `api.py`, `frontend/`, `run_spa.py`, `requirements.txt`, `constraints.txt`, `.env.example`
- Docker: “single-container Streamlit app”; remove “multi-container”
- Data: “Upload PDFs per user; repo does not ship scenario PDFs”
- LICENSE: either add MIT `LICENSE` file matching the badge, or remove the MIT badge
- Logo: add `assets/logo.png` **or** remove the `app.py` reference and use text title only
- CI: list actual steps; do not claim Safety

### 1.4 Seed documents (resolve Copilot vs inspection)

**Choose one and do it completely:**

**Option A (recommended for examiners):** Add 1–3 small, license-clear PDFs under `data/documents/_samples/` (not under a real user id). Document: “Copy into `data/documents/{your_name}/` then rebuild index.” Include a one-page PDF that states “The CEO of INAYAT is …” so `test_agent_query_rag` has a deterministic fact.

**Option B:** Keep `.gitkeep` only. Change README, MASTER, Copilot-style claims, and `backend_feature_test.py` to skip RAG document tests when no files exist (`unittest.skipUnless`).

Do not leave the contradiction.

### 1.5 Verification

- Grep the repo for `3.14`, `19/19`, `gemini-1.5-flash`, `PyVis`, `HealthStatus`, `17-test`, `sample scenario PDF` inside docs; each remaining hit must be historical and labeled superseded.

---

## 2. P1 — CI and packaging alignment

### 2.1 Python and constraints

In `.github/workflows/ci.yml`:

1. Set `python-version: "3.12"` (match Dockerfile).
2. Install with: `pip install -r requirements.txt -c constraints.txt`
3. Keep smoke as the PR gate: `python tests/smoke_test.py`
4. Keep gitleaks, flake8 critical, black.

### 2.2 Optional live integration (do not block every PR)

Add a **second workflow** `integration.yml`:

- `on: workflow_dispatch` and `schedule: cron` (e.g. weekly)
- Same secrets as smoke
- `python tests/backend_feature_test.py`
- Document cost: live Gemini + Mem0 + Neo4j

PR CI stays cheap and deterministic (mocked RAG already in smoke).

### 2.3 Frontend gate (additive)

Add a job `frontend-build`:

- `working-directory: frontend`
- `npm ci` + `npm run build`
- Fail the PR if SPA does not compile

Do not require ESLint until a config exists; adding a linter without a baseline will fail the repo.

### 2.4 pytest

If you add pytest, add it to `requirements.txt` **and** `constraints.txt`. Until then, delete the smoke docstring claim that local runs use pytest, or add pytest as a real extra. Do not advertise a tool that is not installed.

### 2.5 Safety / dependency audit

CONTEXT claimed Safety. Either:

- Add `pip-audit` (maintained) as a CI step, **or**
- Remove the Safety claim from CONTEXT

Do not add the unmaintained `safety` package unless you pin and accept its current status.

### 2.6 Verification

- Fresh CI log shows Python 3.12, constraints used, 21 smoke tests, no false Safety step.
- Docker build still succeeds on 3.12-slim.

---

## 3. P2 — Type-safe settings and identity (core quality laws)

### 3.1 `core/settings.py` (new; single config owner)

Introduce `InayatSettings` (Pydantic v2 `BaseSettings`) loaded once.

**Fields and defaults (all env-driven, zero hardcoded secrets):**

| Field              | Env                       | Default                                       | Notes                  |
| ------------------ | ------------------------- | --------------------------------------------- | ---------------------- |
| `gemini_api_key`   | `GEMINI_API_KEY`          | required                                      | Secret                 |
| `mem0_api_key`     | `MEM0_API_KEY`            | `""`                                          | Optional               |
| `neo4j_uri`        | `NEO4J_URI`               | `""`                                          | Optional               |
| `neo4j_username`   | `NEO4J_USERNAME`          | `"neo4j"`                                     | Not a secret by itself |
| `neo4j_password`   | `NEO4J_PASSWORD`          | `""`                                          | Secret                 |
| `llm_model`        | `INAYAT_LLM_MODEL`        | `gemini-flash-lite-latest`                    | Replaces `_MODEL_NAME` |
| `embed_model`      | `INAYAT_EMBED_MODEL`      | `gemini-embedding-001`                        |                        |
| `chunk_size`       | `INAYAT_CHUNK_SIZE`       | `512`                                         |                        |
| `chunk_overlap`    | `INAYAT_CHUNK_OVERLAP`    | `64`                                          | Must be `< chunk_size` |
| `similarity_top_k` | `INAYAT_TOP_K`            | `5`                                           |                        |
| `mmr_enabled`      | `INAYAT_MMR_ENABLED`      | `false`                                       | Feature flag           |
| `mmr_lambda`       | `INAYAT_MMR_LAMBDA`       | `0.7`                                         |                        |
| `max_upload_bytes` | `INAYAT_MAX_UPLOAD_BYTES` | `10485760`                                    | 10 MiB                 |
| `demo_mode`        | `INAYAT_DEMO_MODE`        | `false`                                       | Gates breaker toggle   |
| `cors_origins`     | `INAYAT_CORS_ORIGINS`     | `http://localhost:5173,http://localhost:8000` | Comma-separated        |
| `log_level`        | `INAYAT_LOG_LEVEL`        | `INFO`                                        |                        |

**Validator:** `chunk_overlap < chunk_size`.  
**Access:** `get_settings()` cached; tests inject via env then cache_clear.

**Migration:** `core/startup.py` `validate_env()` becomes a wrapper: missing Gemini → same `(False, missing_critical, missing_recommended)` tuple so existing tests keep passing.

**`.env.example`:** append the `INAYAT_*` keys with comments. Do not remove the five existing keys.

### 3.2 `core/identity.py` (new)

```
UserId rules:
  - strip whitespace
  - length 1..64
  - charset: [A-Za-z0-9][A-Za-z0-9._-]*
  - reject ".", "..", path separators, NUL
  - reject Windows reserved names (CON, PRN, AUX, NUL, COM1, LPT1, …)
```

`UserId.parse(raw) -> UserId` raises `InvalidUserId` (subclass of `ValueError`).

**Call sites (all of them):**

- `api.py` query, upload, memories, graph
- `app.py` profile name / query param
- `core/agent.py` directory join
- `core/graph_store.py` Cypher parameter (already parameterized; still validate)

**Filesystem:** `os.path.join(_DOC_ROOT, user_id.value)` only after parse. Never interpolate raw query strings into paths.

### 3.3 Typed query contract (backwards compatible)

Add models in `core/schemas.py`:

- `QueryInput`: `question: str` (min 1), `user_id: UserId`, `memory_context: str = ""`
- `QueryResult`: `answer: str`, `route: Literal["rag","llm","apology"]`, `source_count: int`, `used_memory: bool`, `latency_ms: float`

Keep:

```python
def query(question: str, user_id: str = "default", memory_context: str = "") -> str:
    result = query_detailed(QueryInput(...))
    return result.answer
```

**API:** `POST /api/query` returns `QueryResult` JSON. Frontend badges use `route` and `used_memory` — delete heuristic string matching in `AgentWorkspace.jsx`.

**Server memory_context:** Continue to **rebuild from Mem0** (authoritative). Accept client `memory_context` only as a cache hint; never trust it for authorization. Document this in OpenAPI description so the unused-field confusion ends.

---

## 4. P2 — RAG, memory isolation, ingest

### 4.1 Short-term vs long-term (agentic standard)

| Store                                | Contents                             | TTL     | Owner                  |
| ------------------------------------ | ------------------------------------ | ------- | ---------------------- |
| UI / optional `core/conversation.py` | Last N chat turns                    | Session | Presentation           |
| Mem0                                 | Extracted facts, not raw dumps       | Durable | `memory.py`            |
| Neo4j                                | Chunks + entities from **documents** | Durable | `graph_store` + ingest |

**Change Mem0 write path without breaking add_memory signature:**

Keep `add_memory(user_id, text)`. Change the **caller** (api + app) to pass a compact fact line, not the entire utterance, **or** add `add_memory(user_id, text, *, kind="utterance"|"fact")` defaulting to `"utterance"` for compatibility.

Preferred compatible behavior:

1. Still call `add_memory` with the user message (existing tests / Mem0 demo keep working).
2. Additionally call `search_memories(user_id, question, limit=5)` and merge with `get_memories` (cap total chars via settings, e.g. 2000) so search is on the hot path.

If Mem0 search fails, fall back to `get_memories` only (`safe_execute`).

### 4.2 Retrieval upgrades (flagged, default off)

Default stays `similarity_top_k` so current answers do not silently change.

When `INAYAT_MMR_ENABLED=true`, build the query engine with LlamaIndex MMR (`vector_store_query_mode="mmr"` / `mmr_threshold` per installed LlamaIndex 0.14 API). If the installed API rejects the kwarg, log once and fall back to top_k (graceful, no crash).

Do not invent a second vector DB. Hybrid BM25 is a later epic: PropertyGraphIndex already mixes graph + vector. Document that in README so “no BM25” is an informed gap, not a surprise.

### 4.3 Configurable chunking

`configure_llama_settings()` must read `get_settings().chunk_size` and `chunk_overlap` instead of literals 512/64.

**Warning:** Changing chunk size does not rewrite existing Neo4j nodes. Document: “Re-upload / rebuild index after changing chunk settings.”

### 4.4 `from_existing` isolation

When the user folder is empty, **do not** attach the entire graph as that user’s index without filters. `query()` already applies `MetadataFilter`. Keep that filter **unconditional** even for `from_existing`.

Additionally: if `_has_documents` is false **and** vis/query would be empty, skip `from_existing` and return `None` index so the LLM fallback is explicit rather than scanning a shared graph. This is the safer default. Gate with `INAYAT_ALLOW_EMPTY_FROM_EXISTING=false` (default false). Existing demos that rely on a pre-filled Aura graph can set it true.

### 4.5 Ingest: stop blocking the API thread

Split:

1. `save_uploads(user_id, files) -> list[str]` — validate MIME (PDF/TXT), size, sanitize filename (`Path(name).name` only).
2. `build_index(user_id)` — existing logic, per-user lock.
3. API `POST /api/upload`:
   - Save files immediately.
   - Start `BackgroundTasks.add_task(build_index, user_id)` **or** return after sync build if `INAYAT_SYNC_INGEST=true` (default **true** for Streamlit-parity and current tests).
   - When async: return `{status: "accepted", files: [...]}`. Add `GET /api/index-status?user_id=` reading a process-local dict `{user_id: "idle"|"building"|"ready"|"error"}`.

Streamlit keeps sync ingest (spinner). No behavior change for the demo script unless you opt into async.

### 4.6 Disclaimer gate

Keep the phrase list but:

- Only trigger fallback if `source_nodes` is empty **or** (phrases match **and** `source_count == 0`).
- If sources exist, return RAG answer even if the model hedges. This cuts false fallbacks.

Expose `route` so examiners can see RAG vs LLM.

---

## 5. P2 — Graph isolation and breakers

### 5.1 Visualization Cypher

Current: `MATCH (c:Chunk {user_id: $user_id})` plus 1–2 hop neighbors.

**Fix:** Return a neighbor only if:

- it is a `Chunk` with the same `user_id`, or
- it is an `Entity` **and** every connected `Chunk` in the result set has that `user_id`, or
- strip neighbors that have a different `user_id` property.

Never return another user’s `Chunk`. Truncation and embedding stripping stay.

Mock graph (`is_mock: True`) remains when the user has zero chunks.

### 5.2 Shared database (honest production path)

Do **not** create per-user Aura databases in this phase (cost + ops). Document shared-DB + metadata isolation as the demo contract.

Production follow-on (separate epic): `user_id` on every node at write time (LlamaIndex metadata already on chunks; add entity property in a post-index Cypher `SET`).

### 5.3 Circuit breakers: keep global, reduce blast radius

Do not silently change to per-user breakers (would hide real outages).

Changes:

1. `forced_open` writes allowed only if `settings.demo_mode` is true (API 403 otherwise). Streamlit checkboxes same gate.
2. Log `breaker_state` + service name on every transition.
3. Keep one breaker per **service** (Mem0, Neo4j) — that is correct for shared cloud outages.

### 5.4 FastAPI boot

Call `run_startup()` (or health sweep) at FastAPI lifespan startup so `/api/startup` is not `"⚪ Unknown"` until the first health click. Register `close_driver` on shutdown. Streamlit already does this — parity.

---

## 6. P3 — Security and deployment convergence

### 6.1 CORS

Replace `allow_origins=["*"]` + `allow_credentials=True` with `allow_origins=settings.cors_origins` (explicit list). Credentials only if origins are not `*`.

### 6.2 Auth (minimal, backwards compatible)

Add optional `INAYAT_API_KEY`. If empty, current open demo behavior remains. If set:

- Require header `X-INAYAT-KEY` on mutating routes (`/api/query`, `/api/upload`, `/api/memories/clear`, `/api/health/toggle`).
- Streamlit reads the same env and sends the header if you later point it at the API; while Streamlit talks to `core` in-process, the key is unused (in-process is already trusted).

This is not multi-user auth. It stops anonymous internet scrape of Mem0 when the API is exposed.

### 6.3 Docker convergence (migration path)

**Phase 1 (now):** Document two compose profiles without deleting Streamlit:

```yaml
# docker-compose.yml
services:
  inayat-streamlit: # default, current CMD
  inayat-spa: # build frontend, CMD uvicorn api:app --host 0.0.0.0 --port 8000
```

**Phase 2:** Default profile `spa`. README “quick start” uses SPA. Streamlit remains `docker compose --profile streamlit up`.

SPA image must:

- `npm ci && npm run build` in a multi-stage Dockerfile **or** copy prebuilt `frontend/dist`
- Expose 8000
- Healthcheck `GET /api/health` not Streamlit `/_stcore/health`

Keep `data` volume.

### 6.4 `warmup.py`

Stop calling `get_index()` for `"default"` unless that profile exists. Ping Neo4j `RETURN 1` only. Avoid polluting the default tenant.

---

## 7. Observability

Add a small `core/observability.py`:

- `request_id` UUID per API request (middleware) and per Streamlit turn
- Log structured line: `event=query user_id=... route=rag|llm|apology latency_ms=... source_count=... mem0_ok=bool neo4j_ok=bool`
- Do not log full prompts or API keys
- Timing via `time.perf_counter()` around RAG and LLM attempts

Wire into `query_detailed` and `api.py`. Existing `logging_config.py` rotating file stays.

---

## 8. Frontend contract updates

`AgentWorkspace.jsx`:

- Read `route`, `used_memory`, `source_count` from `/api/query`
- Stop inferring RAG from answer text
- Upload: if async ingest is off (default), keep current wait-for-200 behavior
- Graph: show `is_mock` banner when true

`ArchitectureDiagram.jsx`: breaker toggles must handle 403 when demo mode is off (show “enable INAYAT_DEMO_MODE”).

---

## 9. Tests (fully specified; additive)

### 9.1 Keep existing 31 tests green

Do not rename unittest methods. Wrapper `query()` still returns `str`.

### 9.2 New unit tests in `tests/smoke_test.py` (or `tests/test_identity.py` loaded by smoke `__main__`)

Must run **without** API keys:

1. `UserId.parse("Alice")` succeeds
2. `UserId.parse("../etc")` raises
3. `UserId.parse("alice/bob")` raises
4. Settings: `chunk_overlap >= chunk_size` raises validation error (use env + cache_clear)
5. `query_detailed` mock: RAG with sources → `route=="rag"`
6. `query_detailed` mock: no sources → `route=="llm"`
7. Disclaimer + sources present → still `route=="rag"` (new gate)

Update smoke count in README after adding these. Count methods with the same `def test_` convention.

### 9.3 Backend live tests

- Skip RAG CEO test if no files under any documents dir (`skipUnless`)
- After Option A seed PDF, keep the CEO assertion

### 9.4 API tests (optional file `tests/test_api_contract.py`)

Use FastAPI `TestClient`:

- invalid user_id → 400
- toggle breaker without demo mode → 403
- CORS: disallowed origin not reflected (when origins are explicit)

---

## 10. Implementation order (do not skip ahead)

Each step must leave the app bootable.

| Step | Work                                                                   | Compatibility                             |
| ---- | ---------------------------------------------------------------------- | ----------------------------------------- |
| 1    | Canonical docs + STATUS.md + LICENSE or badge fix + logo or remove ref | Docs only                                 |
| 2    | Seed PDF Option A or skipUnless Option B                               | Tests                                     |
| 3    | CI Python 3.12 + constraints + frontend-build job                      | CI                                        |
| 4    | `settings.py` + wire `llm_setup` chunk/model                           | Behavior same at defaults                 |
| 5    | `identity.py` + sanitize all path/API user_ids                         | Invalid names start failing (intended)    |
| 6    | `QueryResult` + wrapper `query()` + API/frontend badges                | Additive JSON fields                      |
| 7    | `search_memories` on hot path with fallback                            | Better memory; still works if Mem0 down   |
| 8    | Vis Cypher user filter tightening                                      | Safer graph                               |
| 9    | FastAPI lifespan health + CORS origins + demo_mode gate                | Demo script needs `INAYAT_DEMO_MODE=true` |
| 10   | Optional API key                                                       | Off by default                            |
| 11   | Compose spa profile + Dockerfile stage                                 | Streamlit still default until you flip    |
| 12   | MMR flag, async ingest flag                                            | Off by default                            |
| 13   | Observability fields                                                   | Logs only                                 |

**Do not** start with multi-agent LangGraph. That is a new product, not a fix.

---

## 11. Mapping: WHAT_TO_FIX punch list → this spec

| #           | Item                       | Section      |
| ----------- | -------------------------- | ------------ |
| 1–14        | Documentation & truth      | §1           |
| 15–21       | Testing & CI               | §2, §9       |
| 22–25       | Config & typing            | §3           |
| 26–34       | RAG / memory / agent       | §4           |
| 35–42       | Isolation & security       | §3.2, §5, §6 |
| 43–46       | Deployment                 | §6.3         |
| 47–48       | Observability              | §7           |
| Keep-list E | Do not delete core modules | §0.3         |

---

## 12. Examiner one-liner (after fixes)

I.N.A.Y.A.T. is a **single-agent, production-pattern RAG system** (Gemini + LlamaIndex PropertyGraphIndex + Neo4j + Mem0) with **documented** dual UIs, **typed** config, **validated** user ids, **CI that matches Docker (Python 3.12)**, and **honest** test counts (**52 smoke** on every PR, **10 live** on schedule). Isolation is **soft multi-tenancy** on a shared graph, which is acceptable for a demo and explicitly not a multi-tenant SaaS.

(The “21 smoke” figure in earlier drafts is superseded; count `def test_` methods in `tests/smoke_test.py`.)

---

## 13. Non-goals (refuse scope creep)

- Rewriting Streamlit into React in one commit
- Per-user Neo4j Aura instances
- LangGraph / CrewAI multi-agent orchestration
- Replacing Mem0 or Neo4j
- Claiming production hardening while auth is optional
- Incomplete snippets or `# TODO` in shipped code

When implementing, ship each step as a complete, importable change with tests from §9 that still run via `python tests/smoke_test.py`.
