# WHAT TO FIX — I.N.A.Y.A.T. Complete Issue Inventory

**Purpose:** Single lossless capture of Copilot’s status report and the Principal Architect deep-dive. This file is analysis only. Remediation lives in `HOW_TO_FIX.md`.

**Repo:** https://github.com/Inayat-0007/I.N.A.Y.A.T.-An-agentic-RAG-system-that-remembers-you-reads-your-documents-and-visualises..git

**Local clone:** `MULTI AGENT/INAYAT`

**Inspection date:** 2026-08-13

**Nature of this request:** Analysis / explanation. No code was changed as part of the original status work.

---

## A. Copilot status (verbatim meaning, preserved in full)

This request is analysis/explanation, not a code-change task.

### Current deep status of the project (from repo inspection)

**Overall maturity:** Advanced MVP / demo-ready architecture with production-style patterns.

**Core backend exists and is structured:** `core/` has agent, memory, graph store, health, resilience, startup, logging modules.

**Two app surfaces coexist:**
- `app.py` = full Streamlit app
- `api.py` + `frontend/` = FastAPI + React SPA path (modern UI route)

**RAG pipeline is implemented:** LlamaIndex PropertyGraphIndex + Neo4j + Gemini + Mem0, with fallback routing when services fail.

**Resilience features are implemented:** custom circuit breaker, safe execution wrappers, health checks, startup env validation.

**User isolation is implemented:** per-user document folders and user-scoped memory/graph querying.

**Knowledge graph visualization exists:** graph data API and UI integration are present (not just placeholder docs).

**Testing status (codebase level):**
- `tests/smoke_test.py` exists (CI-oriented)
- `tests/backend_feature_test.py` exists (deeper integration coverage)
- CI workflow currently runs lint + secrets scan + smoke test.

**DevOps/packaging:** Dockerfile + docker-compose present, plus `run_spa.py` for local dual-server dev mode.

**Data status (Copilot claim):** `data/documents/` already contains sample scenario PDFs, so RAG has seed docs in repo.

**Important current inconsistencies / risks**
- Documentation drift: `README.md`, `CONTEXT.md`, and `MASTER_DEEP_DIVE_REPORT.txt` do not fully agree (test counts, what is “missing,” UI state, etc.).
- Python version mismatch across files: README badge (3.14), CI (3.11), Docker (3.12), docs mixed.
- CI scope gap: CI does not run the full backend integration test suite by default.

**Practical status conclusion (Copilot):** The project is feature-rich and close to production-demo quality, but needs a documentation/consistency cleanup and CI alignment to present a single, trustworthy “current status” to reviewers/examiners.

---

## B. Principal Architect deep dive (preserved in full)

Repo cloned and inspected at `MULTI AGENT/INAYAT`. Copilot’s maturity assessment is **accurate**: this is an **advanced MVP / demo-ready** system with production-style patterns, not yet a hardened production deployment.

### Executive Verdict

| Dimension | Grade | Notes |
|-----------|-------|-------|
| **Architecture** | B+ | Clean `core/` separation; dual UI surfaces share one backend |
| **RAG implementation** | B | Real PropertyGraphIndex + Neo4j + Mem0; not a stub |
| **Resilience** | A- | Custom circuit breakers, retries, graceful degradation |
| **Multi-tenancy** | C+ | Soft isolation by `user_id` string — no auth, shared Neo4j DB |
| **Testing** | B- | 31 tests exist; CI only runs 21 smoke tests |
| **Documentation** | D+ | Significant drift across README, CONTEXT, MASTER report |
| **DevOps** | B | Docker + CI + constraints; Python version mismatch |

**Bottom line:** Feature-rich and examiner-demo ready. Needs a **documentation truth pass** and **CI alignment** before it presents as a single trustworthy status to reviewers.

---

### 1. System Architecture (Component Boundaries)

```
Presentation:
  app.py Streamlit :8501
  frontend/ React + Vite :5173
  api.py FastAPI :8000

core/ (shared business logic):
  agent.py          RAG + query
  llm_setup.py      Gemini LLM + embeddings
  memory.py         Mem0 client
  graph_store.py    Neo4j + vis data
  resilience.py     CircuitBreaker
  health.py + startup.py

External:
  Gemini API
  Mem0 Cloud
  Neo4j AuraDB
```

**Data flow between surfaces:**
- Streamlit → agent / memory / graph_store
- SPA → FastAPI → agent / memory / graph_store
- agent → llm_setup + graph_store
- llm_setup → Gemini
- memory → Mem0
- graph_store → Neo4j
- memory + graph_store → resilience

#### Boundary discipline (good)

- **LLM execution** (`llm_setup.py`) — decoupled from retrieval
- **Vector/graph retrieval** (`agent.py` + `graph_store.py`) — decoupled from UI
- **Document parsing** — LlamaIndex `SimpleDirectoryReader` inside `build_index()`
- **Visualization** — `get_visualization_data()` returns vis-network JSON; UI renders it

#### Boundary gaps (architectural debt)

- **No Pydantic models in `core/`** — request validation only at the FastAPI layer (`api.py`); agent functions use raw strings
- **No separate ingest service** — upload → disk → synchronous `build_index()` blocks the API request
- **Global circuit breakers** — one user's forced failure affects all users on that process
- **"Agentic" is marketing, not architecture** — single `query()` function, no tool-calling loop, no planner

---

### 2. Data Flow: End-to-End Query Path

```
User message
    │
    ├─► add_memory(user_id, text)          → Mem0 Cloud (long-term)
    ├─► get_memories(user_id)              → bullet-list context string
    │
    └─► agent.query(question, user_id, memory_ctx)
            │
            ├─ Attempt 1: PropertyGraphIndex RAG
            │     • chunk_size=512, overlap=64 (llm_setup.py)
            │     • gemini-embedding-001 (3072-dim)
            │     • similarity_top_k=5 + MetadataFilter(user_id)
            │     • Disclaimer phrase gate → reject weak answers
            │
            ├─ Attempt 2: Direct Gemini complete(augmented)
            │
            └─ Attempt 3: Static apology string
```

The RAG quality gate in `core/agent.py` is a pragmatic pattern:
- `MetadataFilters` / `MetadataFilter(key="user_id", value=user_id)`
- `index.as_query_engine(include_text=True, similarity_top_k=5, filters=filters)`
- Disclaimer phrases: `"does not contain"`, `"no information"`, `"don't have"`, `"not mentioned"`, `"not clear"`, `"does not mention"`, `"cannot find"`
- If no `source_nodes` OR disclaimer match → treat as miss, fall back to LLM

**What's missing vs. agentic RAG best practices:**
- No **MMR** (Maximal Marginal Relevance) — only `similarity_top_k=5`
- No **hybrid BM25 + vector** — relies on LlamaIndex PropertyGraphIndex internals
- Chunk size is **hardcoded** in `configure_llama_settings()`, not env-configurable
- `search_memories()` exists but is **never called** by app or API — Mem0 search is dead code in the hot path

---

### 3. Dual UI Surfaces (Coexistence, Not Convergence)

| Surface | Entry | Docker default | Maturity |
|---------|-------|----------------|----------|
| **Streamlit** | `app.py` | **Yes** (`CMD streamlit run app.py`) | Full-featured, demo-oriented |
| **React SPA** | `run_spa.py` → `api.py` + Vite | No | Modern UI, production path |
| **FastAPI only** | `uvicorn api:app` | No | Serves built `frontend/dist/` |

This is a **forked presentation layer**, not a migration. Docker still ships Streamlit. The React path is the architecturally cleaner surface (REST API, Pydantic models, CORS, static mount) but is not the default deployment artifact.

---

### 4. User Isolation — Soft Multi-Tenancy

| Layer | Mechanism | Risk |
|-------|-----------|------|
| Documents | `data/documents/{user_id}/` | No `user_id` sanitization (path traversal possible) |
| RAG filter | `MetadataFilter(key="user_id")` | Depends on metadata surviving indexing |
| Neo4j | **Shared database** for all users | Entity nodes 1–2 hops from chunks may leak cross-user context in graph vis |
| Mem0 | API-scoped `user_id` | Anyone who guesses a name can query that profile |
| Chat history | Streamlit `session_state` / React `localStorage` | Client-only, not server-persisted |
| Auth | **None** | Display name = identity |

For a university demo this is acceptable. For production it is a **blocker**.

---

### 5. Resilience Layer (Strongest Engineering)

Custom `CircuitBreaker` in `core/resilience.py`:
- States: CLOSED → OPEN (3 failures) → HALF_OPEN (60s) → CLOSED
- Applied to **Mem0** and **Neo4j Cypher**, not Gemini
- `forced_open` flag for live demo of graceful degradation (sidebar + `/api/health/toggle`)
- Gemini uses **tenacity** retries (6 attempts, exponential backoff) on embedding/LLM calls
- `safe_execute()` wraps all external calls — UI never sees stack traces

Health model: only **Gemini is critical**. Mem0 and Neo4j can be down and the app still responds (degraded).

---

### 6. Testing & CI — Validated Inconsistencies

#### Actual test inventory

| File | Tests | CI runs? | Needs live APIs? |
|------|-------|----------|------------------|
| `tests/smoke_test.py` | **21** | **Yes** | 3 optional live pings |
| `tests/backend_feature_test.py` | **10** | **No** | Yes (all) |
| **Total** | **31** | 21 | — |

Smoke tests (`tests/smoke_test.py`) — 21 methods:
- `TestImports` (8): import resilience, logging_config, llm_setup, memory, graph_store, agent, health, startup
- `TestEnvironment` (1): `validate_env()` returns `(bool, list, list)` — does **not** require secrets
- `TestHealthMonitor` (1): `HealthMonitor()` has keys `gemini`, `mem0`, `neo4j`
- `TestResilience` (6): `safe_execute` success/fallback; breaker open/reset; HALF_OPEN single probe; thread safety
- `TestLiveServices` (3): live `ping_gemini` / `ping_mem0` / `ping_neo4j` — **skipped** if keys missing or contain `"dummy"`
- `TestAgentPipeline` (2): **mocked** RAG success + RAG-fail → LLM fallback

Backend integration (`tests/backend_feature_test.py`) — 10 methods:
- `TestBackendStartup` (2): `run_startup()` ok + health keys; `validate_env()` must have **no** missing critical vars
- `TestBackendLLM` (2): Gemini complete `"verified"`; embedding length **3072**
- `TestBackendResilience` (1): Breaker OPEN → HALF_OPEN after timeout → CLOSED
- `TestBackendMemory` (1): Mem0 add/get/search with up to 15s polling
- `TestBackendGraphStore` (2): `SHOW DATABASES`; vis payload keys `nodes`/`edges`/`is_mock`
- `TestBackendAgentRAG` (1): Live query CEO of INAYAT + `"What is 5 + 5?"` contains `"10"`
- `TestBackendHealth` (1): All three services `"🟢 Connected"`

**CI does not run `backend_feature_test.py`.**

`pytest` is mentioned in smoke docstring but **is not in `requirements.txt`.** Smoke `__main__` loads unittest classes. CI runs `python tests/smoke_test.py`.

#### Documentation claims vs. reality

| Claim (source) | Reality |
|----------------|---------|
| README badge: "19/19 passed" | Smoke suite has **21** tests |
| README L130–131: smoke **19**, backend **10** | Smoke **21**; backend **10** is correct |
| MASTER: "17-test suite" / “Present 17-test suite”; “lacks mocked LLM” | Smoke has **21**, including **mocked RAG** |
| README badge: Python **3.14** | CI uses **3.11**, Docker uses **3.12** |
| MASTER: Python **3.14.3** venv | Not aligned with CI/Docker |
| CONTEXT: Python **3.11** | Matches CI only |
| README: Gemini **1.5 Flash** / `gemini-1.5-flash` | Code: `_MODEL_NAME = "gemini-flash-lite-latest"` (`core/llm_setup.py`) |
| `llm_setup.py` docstring still says 1.5 Flash | Code uses `gemini-flash-lite-latest` |
| `graph_store.py` mock uses `"gemini-3.1-flash-lite"` | Third model string |
| README: sample PDFs in `data/documents/` | Only `.gitkeep` — **no seed docs in repo** |
| README: `assets/logo.png` | **`assets/` directory missing** (`app.py` still references it) |
| README: `inayat_project_deep_dive.pdf`, `inayat_technical_architecture.pdf` | Present at **repo root**, not necessarily where README tree claims |
| README: `LICENSE` / MIT badge | **LICENSE file absent** |
| CONTEXT: Safety dependency audit in CI | **Not present** in `ci.yml` |
| CONTEXT: push to **`main` only** | CI watches **`main` and `master`** |
| CONTEXT file map lists only `tests/smoke_test.py` | Omits `backend_feature_test.py` |
| CONTEXT: `HealthStatus` class | Health module is `HealthMonitor` |
| CONTEXT: **PyVis** graph tab | README: **Vis.js**; MASTER: **graph visual omitted** |
| MASTER: no in-app upload | README: isolated ingest + ingest PDF in demo; repo has `frontend/` + `api.py` upload |
| MASTER: startup blocks if **all** critical keys missing | Code critical list is **Gemini only** |
| README: "multi-container" docker-compose | **Single service** only (`inayat-app`) |
| README versions: Streamlit `^1.43.0`, Mem0 `^0.1.0`, LlamaIndex `^0.12.0` | constraints: Streamlit **1.58.0**, mem0ai **2.0.4**, llama-index-core **0.14.22** |
| README tree omits | `requirements.txt`, `constraints.txt`, `.env.example`, `frontend/`, `api.py`, `run_spa.py`, `demo_script.md` |

#### CI pipeline (actual `.github/workflows/ci.yml`)

- Triggers: push/PR to `main` and `master`
- Job: `lint-and-test` on `ubuntu-latest`
- Python: **3.11** via `actions/setup-python@v6`
- Install: `pip install -r requirements.txt` — **no `-c constraints.txt`**
- Runs:
  1. flake8 critical only: `E9,F63,F7,F82`
  2. `black --check --diff .`
  3. `gitleaks/gitleaks-action@v2`
  4. `python tests/smoke_test.py` with GitHub Secrets for Gemini/Mem0/Neo4j
- **Does not run:** `backend_feature_test.py`, Safety/dependency audit, pytest, frontend build/lint

---

### 7. Dependency & Environment Posture

**Required env vars** (`.env.example`):
- `GEMINI_API_KEY` — **critical** (startup blocks without it)
- `MEM0_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` — recommended

**Good:** No hardcoded secrets; `validate_env()` at startup; Gitleaks in CI.

**Gap:** No Pydantic `BaseSettings` — uses `python-dotenv` + manual `os.getenv()`. Works, but not type-safe config.

**`requirements.txt`:** `-c constraints.txt` then unpinned names: `streamlit`, `google-generativeai`, LlamaIndex (`core`, `llms-google-genai`, `embeddings-google-genai`, `graph-stores-neo4j`), `mem0ai`, `neo4j`, `tenacity`, `python-dotenv`, `flake8`, `black`. No pytest, no Safety.

**`constraints.txt` pins:** streamlit **1.58.0**, google-generativeai **0.8.6**, llama-index-core **0.14.22**, mem0ai **2.0.4**, neo4j **5.28.4**, tenacity **9.1.4**, python-dotenv **1.2.2**, flake8 **7.3.0**, black **26.5.1**, plus pillow **12.2.0**, numpy **2.4.6**.

---

### 8. What Is Genuinely Implemented (Not Placeholder)

| Feature | Status | Evidence |
|---------|--------|----------|
| PropertyGraphIndex RAG | **Real** | `core/agent.py` `build_index()` + `query()` |
| Neo4j graph store | **Real** | `Neo4jPropertyGraphStore`, Cypher vis query |
| Mem0 long-term memory | **Real** | `MemoryClient` add/get/clear |
| Circuit breaker degradation | **Real** | Demo toggles + live fallback |
| Graph visualization | **Real** | vis-network payload from Neo4j chunks |
| React SPA | **Real** | `frontend/src/` with AgentWorkspace, upload, graph drawer |
| FastAPI REST layer | **Real** | 8+ endpoints in `api.py` |
| Docker packaging | **Real** | `Dockerfile` + `docker-compose.yml` |
| PDF deep-dive docs | **Real** | `inayat_project_deep_dive.pdf`, `inayat_technical_architecture.pdf` in repo root |

---

### 9. Production Readiness Gaps (Prioritized)

#### P0 — Trust & consistency
1. **Single source of truth doc** — reconcile README, CONTEXT, MASTER into one `STATUS.md`
2. **Fix test count badges** — 21 smoke + 10 integration = 31 total
3. **Align Python version** — pick 3.12 (Docker) or 3.11 (CI), update all references
4. **Add seed documents** or document that RAG demo requires manual upload

#### P1 — CI hardening
5. Run `backend_feature_test.py` on a scheduled workflow (not every PR — needs secrets + cost)
6. Install with `-c constraints.txt` in CI (matches Docker)
7. Add frontend `npm run build` step to catch SPA breakage

#### P2 — Architecture hardening
8. Add `user_id` sanitization (alphanumeric + slug only)
9. Make chunk_size/overlap/top_k **env-configurable**
10. Wire `search_memories()` into the query path (semantic memory retrieval, not just `get_all`)
11. Add Pydantic `Settings` class for typed config
12. Per-user Neo4j subgraph isolation or database-per-tenant for real multi-tenancy

#### P3 — Deployment convergence
13. Pick **one** default UI (recommend React + FastAPI)
14. Update Docker `CMD` to `uvicorn api:app` + serve `frontend/dist/`
15. Add auth layer (even basic API key per user)

---

### 10. Revised Maturity Statement

> **INAYAT is a well-structured, demo-grade agentic RAG system** with real LlamaIndex PropertyGraphIndex integration, Mem0 memory, Neo4j knowledge graph, custom resilience patterns, and a modern React SPA path. It demonstrates production-aware engineering (circuit breakers, health checks, graceful degradation, user-scoped retrieval) but operates as a **single-agent RAG pipeline**, not a multi-agent orchestrator. Documentation drift and CI scope gaps are the primary risks for external reviewers — the code itself is substantially more complete than the oldest docs suggest.

Copilot’s provided status summary holds up under inspection. **The main correction:** `data/documents/` has no sample PDFs (only `.gitkeep`), so out-of-the-box RAG requires either prior Neo4j indexing or manual upload.

---

## C. Additional architecture facts (must not be lost)

### Directory tree (top 3 levels)

```
INAYAT/
├── app.py                 # Streamlit UI (legacy / Docker default)
├── api.py                 # FastAPI REST + SPA static host
├── run_spa.py             # Dev: uvicorn :8000 + Vite :5173
├── warmup.py              # Keepalive / pre-index
├── requirements.txt
├── constraints.txt
├── docker-compose.yml
├── Dockerfile             # CMD: streamlit run app.py :8501
├── .env.example
├── README.md, CONTEXT.md, demo_script.md, RGPV_*.md
├── activate.ps1
├── .github/workflows/ci.yml
├── core/
│   ├── __init__.py
│   ├── agent.py
│   ├── graph_store.py
│   ├── health.py
│   ├── llm_setup.py
│   ├── logging_config.py
│   ├── memory.py
│   ├── resilience.py
│   └── startup.py
├── data/documents/.gitkeep   # per-user dirs created at runtime: data/documents/{user_id}/
├── frontend/src/components/  # LandingPage, AgentWorkspace, ArchitectureDiagram, …
├── frontend/dist/            # production Vite build (served by api.py)
├── tests/smoke_test.py
├── tests/backend_feature_test.py
└── scratch/debug_vis.py
```

### `core/` module responsibilities

| File | Role |
|------|------|
| `__init__.py` | Package docstring listing submodules. No exports. |
| `startup.py` | Boot: `load_env()`, `setup_logging()`, `validate_env()`, `HealthMonitor.run_all()`, `atexit.register(close_driver)`. Critical: `GEMINI_API_KEY`. Recommended: Mem0 + Neo4j vars. |
| `logging_config.py` | Logger `"inayat"`: stdout + rotating `inayat_debug.log` (3×5 MB). Idempotent handlers (Streamlit reruns). |
| `llm_setup.py` | Gemini LLM + embeddings; LlamaIndex global `Settings`. Models: `_MODEL_NAME = "gemini-flash-lite-latest"`, `_EMBED_MODEL = "gemini-embedding-001"`. `ResilientGoogleGenAIEmbedding` / `ResilientGoogleGenAI` retry **6 times**. `Settings.chunk_size = 512`, `Settings.chunk_overlap = 64`. |
| `agent.py` | Document load, `PropertyGraphIndex` build/cache, `query()` RAG + LLM fallback. `_indices` dict + `_indices_lock`. Empty folder → `PropertyGraphIndex.from_existing(...)`. |
| `memory.py` | Mem0 `MemoryClient` CRUD keyed by `user_id`. Circuit breaker threshold 3 / recovery 60s. `search_memories` unused by app/api. |
| `graph_store.py` | Neo4j driver, Cypher, `Neo4jPropertyGraphStore`, vis-network payload. Session `database=NEO4J_USERNAME` (usually `"neo4j"`), **not** app `user_id`. Empty vis → mock architecture graph (`is_mock: True`). |
| `resilience.py` | `CircuitBreaker`, `@resilient_call` (tenacity), `safe_execute`. HALF_OPEN allows **one** probe. |
| `health.py` | `HealthMonitor` probes Gemini / Mem0 / Neo4j. `all_critical_up()`: **only Gemini** must be UP. |

### Entry-point differences

| | `app.py` | `api.py` | `run_spa.py` |
|---|---|---|---|
| **What** | Streamlit full UI | FastAPI backend + optional React `frontend/dist` | Dev process manager |
| **Launch** | `streamlit run app.py` | `uvicorn api:app --port 8000` | `python run_spa.py` |
| **Docker** | **Yes** | No | No |
| **Startup** | Full `run_startup()` (health + atexit Neo4j close) | Env validate only; health stays `"⚪ Unknown"` until `/api/health` | Spawns both servers |
| **Chat** | `st.session_state.messages`; last user msg triggers agent | `POST /api/query` | N/A |
| **Ingest** | Sidebar `file_uploader` → disk → `build_index` | `POST /api/upload` | N/A |
| **Graph** | Inline vis-network HTML iframe | `GET /api/graph` | N/A |
| **Breakers** | Checkboxes set `mem._cb.forced_open` / `gs._cb.forced_open` | `POST /api/health/toggle` | N/A |

**`api.py` routes**
- `GET /api/startup` — `{ok, health, warnings}`
- `GET /api/health` — live `HealthMonitor.run_all()` + breaker flags
- `POST /api/health/toggle` — `{service: mem0|neo4j, forced}`
- `GET /api/memories?user_id=`
- `POST /api/memories/clear?user_id=`
- `GET /api/graph?user_id=` — `get_index(user_id)` then vis data
- `POST /api/query` — `QueryRequest(question, user_id, memory_context)` — **server ignores client `memory_context` and rebuilds from Mem0**
- `POST /api/upload` — Form `user_id` + files; PDF/TXT only; **sync** `build_index`
- Mount `/` → `frontend/dist` if present

**`run_spa.py`:** daemon threads — uvicorn `api:app` `:8000`, then `npm run dev` in `frontend/` (`:5173`, Vite proxies `/api` → 8000).

### RAG pipeline details

There is no separate ingest service. Flow is **UI/API → filesystem → LlamaIndex PropertyGraphIndex → Neo4j**.

1. Files land in `data/documents/{user_id}/{filename}` (`app.py` skip-if-exists; `api.py` overwrite).
2. `build_index(user_id)`:
   - `SimpleDirectoryReader(user_dir).load_data()`
   - Each `Document.metadata["user_id"] = user_id`
   - `PropertyGraphIndex.from_documents(docs, property_graph_store=graph_store, show_progress=True)`
3. LlamaIndex chunks at 512 tokens, overlap 64, embeds with `gemini-embedding-001`, extracts entities/relations with Gemini LLM, writes to Neo4j.
4. Index object cached in `_indices[user_id]`.
5. If folder empty: `PropertyGraphIndex.from_existing` (whole store, not a per-user subgraph).

Embeddings are **not** a local FAISS/Chroma index; they live in the Neo4j property graph. Tests expect embedding dim **3072**.

### Agent orchestration (not multi-agent)

Not a planner/tool-calling loop. One function, two attempts.

**Streamlit after a user message:**
1. `add_memory(user_id, prompt)` — raw utterance to Mem0
2. `_fetch_memories` (Streamlit cache TTL 30s) → bullet list `memory_ctx`
3. `agent_query(prompt, user_id, memory_context=memory_ctx)`
4. Append assistant message; trim history to last **20**

**FastAPI `api_query_agent`:**
1. `add_memory(user_id, question)`
2. `get_memories` → `memory_ctx`
3–4. `agent_query(...)` (RAG then LLM)
5. Return `{answer, memory_context, memories}`

No tool registry, no sub-agents, no conversation history sent to the LLM (only Mem0 facts + current question). Chat transcript is UI-only.

### Memory system

**Mem0 (long-term)**
- Cloud `MemoryClient`; all ops scoped with `user_id`
- **Write:** every chat turn stores the **full user message**, not a separate fact extractor
- **Read:** `get_all` for pills/context; `search_memories` exists but **unused** by app/api
- **Clear:** `clear_memories` / `/api/memories/clear`
- Failures: empty list / `False`; agent still answers without personalization

**Conversation state (short-term)**

| UI | Storage | Isolation key |
|----|---------|----------------|
| Streamlit | `st.session_state.messages` + `messages_{name}` on profile switch; `?user=` query param | browser session |
| React | `localStorage["messages_${userId}"]` | browser origin + userId |

Neither backend persists chat history. `QueryRequest.memory_context` is unused on the server; SPA still sends it, then overwrites from Mem0.

### Graph store extra facts

- Credentials: `NEO4J_URI`, `NEO4J_USERNAME` (default `neo4j`), `NEO4J_PASSWORD`
- **One Aura database** (`database=NEO4J_USERNAME`). All users share it.
- Direct Cypher: `run_cypher` + vis query on `:Chunk {user_id}`
- Visualization: vis-network groups Agent/LLM/Memory/GraphStore/Resilience/User/Entity/Chunk; mock graph if no chunks
- `warmup.py`: `RETURN 1 AS ping` to keep free-tier Aura awake; `get_index()` (default user)

### Isolation gaps (extra)

- Streamlit warmup: `get_index()` with default `"default"`, not the logged-in user
- `from_existing` loads the **entire** graph store, then query-time filter is the isolation
- Anyone who knows/guesses a name can query that profile’s Mem0 + docs via the API
- Circuit breakers are **global** — one user’s force-fail affects everyone on that process
- No sanitization of `user_id` (path traversal risk)

### Frontend (`frontend/`)

**Stack:** React 18, Vite 5, Tailwind, Framer Motion, Lucide, vis-network.

**Routing:** no React Router. `App.jsx` `activeView`: `'landing' | 'agent'`. `?user=` on load → agent workspace.

- `main.jsx` — `ReactDOM.createRoot` + `App`
- `App.jsx` — navbar, `GET /api/startup` gate, `LandingPage` + `ArchitectureDiagram` + `FeaturesShowcase`, or `AgentWorkspace`; `ProductTour` overlay
- `LandingPage.jsx` — marketing + profile name → `onEnterWorkspace`
- `AgentWorkspace.jsx` — Chat → `POST /api/query`; Memories → `GET /api/memories`; clear → `POST /api/memories/clear`; Health / breakers → `/api/health`, `/api/health/toggle`; Upload → `POST /api/upload`; Graph drawer → `GET /api/graph`; heuristic badges `isRag` / `isMemory` from answer text (not backend flags)
- `ArchitectureDiagram.jsx` — 6-step story + live breaker toggles
- Vite: `server.port 5173`, `proxy /api → localhost:8000`. Production: `npm run build` → `dist/`, served by FastAPI.

### Docker extra facts

**Dockerfile:** `python:3.12-slim`; installs with `-c constraints.txt`; non-root `appuser`; tini; Streamlit on **8501**; healthcheck `http://localhost:8501/_stcore/health`; `CMD ["streamlit", "run", "app.py"]`

**docker-compose.yml:** one service `inayat-app` / `inayat_agent`; port `8501:8501`; volume `./data:/app/data`; `env_file: .env`; `restart: always`

### Data status correction (Copilot vs inspection)

| Source | Claim |
|--------|--------|
| Copilot | `data/documents/` already contains sample scenario PDFs |
| Inspection | Only `data/documents/.gitkeep` |
| MASTER | Place 3–5 PDFs there |
| `backend_feature_test.py` | Assumes an indexed scenario PDF (CEO of INAYAT) that is **not** in the repo |

**This is a factual disagreement that must be fixed in docs and/or by adding seed files.**

### FastAPI vs Streamlit startup inconsistency

- Streamlit calls full `run_startup()` (health + atexit Neo4j close)
- FastAPI only calls `load_env()` + `validate_env()`; health stays `"⚪ Unknown"` until `/api/health`

### CORS / security notes

- FastAPI CORS: `allow_origins=["*"]` with `allow_credentials=True` (unsafe combination)
- No authentication on any API route
- Health toggle can force-open breakers for the whole process

---

## D. Master punch list (every item to fix)

Use this as the checklist. How to fix each item is in `HOW_TO_FIX.md`.

### Documentation & truth
1. Reconcile README, CONTEXT, MASTER into one trustworthy status
2. Fix test-count badges (19 vs 17 vs 21 vs 31)
3. Fix Python version claims (3.14 vs 3.11 vs 3.12)
4. Fix Gemini model name claims vs `gemini-flash-lite-latest`
5. Fix dependency version claims vs `constraints.txt`
6. Fix CI claims (Safety missing; `master` also watched)
7. Fix HealthStatus vs HealthMonitor naming
8. Fix PyVis vs Vis.js vs “graph omitted”
9. Fix upload “missing” vs actually present
10. Fix LICENSE badge vs missing LICENSE file
11. Fix README tree omitting `frontend/`, `api.py`, `run_spa.py`, constraints
12. Fix `assets/logo.png` missing while `app.py` references it
13. Fix seed-PDF claim vs `.gitkeep` only
14. Document that “agentic” is a single-agent RAG pipeline, not multi-agent orchestration

### Testing & CI
15. CI does not run `backend_feature_test.py`
16. CI does not use `-c constraints.txt`
17. CI Python 3.11 vs Docker 3.12
18. No frontend build/lint in CI
19. No Safety/dependency audit despite CONTEXT claim
20. pytest advertised but not in requirements
21. Live RAG test depends on missing seed PDF

### Config & typing
22. No Pydantic Settings; raw `os.getenv`
23. No Pydantic models in `core/` (only FastAPI layer)
24. Chunk size / overlap / top_k hardcoded
25. `QueryRequest.memory_context` ignored by server

### RAG / memory / agent
26. No MMR
27. No hybrid BM25 + vector
28. `search_memories()` unused on hot path
29. Full user utterance stored in Mem0 (no fact extraction)
30. No conversation history sent to LLM
31. Synchronous blocking `build_index` on upload
32. Empty-folder `from_existing` loads entire graph store
33. Disclaimer-phrase quality gate is brittle (false positives/negatives)
34. Heuristic `isRag` / `isMemory` badges are client-side, not backend flags

### Isolation & security
35. No auth; display name = identity
36. No `user_id` sanitization (path traversal)
37. Shared Neo4j database; 1–2 hop vis may leak related nodes
38. Guessable `user_id` can query Mem0 + docs via API
39. Global circuit breakers (cross-user blast radius)
40. CORS `*` + credentials
41. FastAPI health not run at boot
42. Streamlit warmup indexes `"default"` user

### Deployment
43. Dual UI not converged; Docker still Streamlit-only
44. docker-compose is single-container, not multi-container
45. Docker healthcheck is Streamlit-only (`/_stcore/health`)
46. No FastAPI/uvicorn path in Docker CMD

### Observability
47. No structured token usage / latency metrics on query path
48. Logging exists (`inayat_debug.log`) but no request-id / user-id correlation standard

---

## E. What is already good (do not “fix” by deleting)

Keep and extend; do not rip out:
- `core/` modular split (agent, memory, graph, health, resilience, startup, logging)
- Dual-surface coexistence until a migration path exists
- PropertyGraphIndex + Neo4j + Gemini + Mem0 real integration
- Custom CircuitBreaker + `safe_execute` + tenacity retries
- Health checks and env validation
- Per-user document folders + metadata filter
- Graph vis API + UI (not a placeholder)
- Smoke tests + deeper backend tests (even if CI only runs smoke)
- Dockerfile + compose + `run_spa.py`
- Gitleaks in CI
- No hardcoded secrets in source
- Graceful RAG → LLM → apology fallback

---

## F. Suggested next-step options (from original deep dive)

1. Produce a reconciled `STATUS.md` that becomes the single truth document
2. Align CI to run the full test matrix with correct Python version
3. Architect a migration plan from Streamlit-default to FastAPI+React-default Docker deployment

Those options are specified as executable architecture in `HOW_TO_FIX.md`.
