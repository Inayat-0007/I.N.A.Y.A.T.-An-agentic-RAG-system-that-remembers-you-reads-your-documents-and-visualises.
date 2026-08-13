<h1 align="center">🧠 I.N.A.Y.A.T.</h1>
<p align="center">
  <strong>Intelligent Neural Architecture for Yielding Agentic Thinking</strong><br>
  <em>Single-agent RAG with isolated user memory, property-graph retrieval, and self-healing resilience.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/Tests-59%20smoke%20%2F%2010%20live-success" alt="Tests">
  <img src="https://img.shields.io/badge/CI-smoke%20%2B%20frontend-informational" alt="CI Scope">
  <img src="https://img.shields.io/badge/Docker-SPA%20%3A8000-blue?logo=docker&logoColor=white" alt="Docker Ready">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License">
  <br>
  <img src="https://img.shields.io/badge/UI-Streamlit%20%2B%20React-FF4B4B" alt="Dual UI">
  <img src="https://img.shields.io/badge/Database-Neo4j-008CC1?logo=neo4j&logoColor=white" alt="Neo4j AuraDB">
  <img src="https://img.shields.io/badge/Memory-Mem0-purple" alt="Mem0 Memory">
  <img src="https://img.shields.io/badge/LLM-Gemini%20Flash%20Lite-4285F4?logo=google-gemini&logoColor=white" alt="Google Gemini">
</p>

---

## Canonical status (source of truth)

| Fact                | Value                                                                                    |
| ------------------- | ---------------------------------------------------------------------------------------- |
| **Maturity**        | Advanced MVP / demo-ready. **Share via Docker Compose** — not a Kubernetes/SaaS cluster |
| **Agent model**     | Single-agent RAG pipeline (not LangGraph/CrewAI multi-agent)                             |
| **Python**          | 3.12                                                                                     |
| **LLM**             | `gemini-flash-lite-latest`                                                               |
| **Embeddings**      | `gemini-embedding-001` (3072-dim)                                                        |
| **Chunking**        | size 512, overlap 64 (env: `INAYAT_CHUNK_SIZE`, `INAYAT_CHUNK_OVERLAP`)                  |
| **Retrieval**       | PropertyGraphIndex, `similarity_top_k=5`, `user_id` metadata filter                      |
| **Tests**           | 59 smoke (`tests/smoke_test.py`) + 10 live (`tests/backend_feature_test.py`)             |
| **CI**              | flake8 (E9,F63,F7,F82) + black + gitleaks + pip-audit + smoke + frontend build           |
| **Docker**          | `docker compose up --build` → SPA `:8000`. Streamlit: `--profile streamlit` `:8501`. No k8s. |
| **Seed docs**       | `data/documents/_samples/` (MIT); copy into `data/documents/{your_name}/`                |
| **UIs**             | Streamlit (`app.py`) and FastAPI+React (`api.py`, `frontend/`)                           |
| **User ids**        | `UserId.parse()` — letters, digits, `.` `_` `-`; **underscores, not spaces**             |
| **Ingest**          | PDF `%PDF` + pypdf extract; incremental insert; sync by default                          |
| **Isolation**       | Soft: folder + metadata + Mem0 `user_id`; **shared Neo4j DB**; optional `INAYAT_API_KEY` |
| **Critical env**    | `GEMINI_API_KEY`                                                                         |
| **Recommended env** | `MEM0_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`                          |

**Examiner one-liner:** I.N.A.Y.A.T. is a single-agent, production-pattern RAG system (Gemini + LlamaIndex PropertyGraphIndex + Neo4j + Mem0) with documented dual UIs (Streamlit `:8501` + React SPA `:8000`), typed config, validated user ids (underscores, not spaces), incremental PDF ingest, CI that matches Docker (Python 3.12), and honest test counts (59 smoke on every PR, 10 live on schedule). Isolation is soft multi-tenancy on a shared graph — acceptable for a demo, not a multi-tenant SaaS.

See also: [STATUS.md](STATUS.md) (one-page examiner sheet).

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Share this project](#-share-this-project)
3. [What this repo now includes](#-what-this-repo-now-includes)
4. [System Architecture](#-system-architecture)
5. [Tech Stack](#️-tech-stack)
6. [Project Structure](#-project-structure)
7. [Key Features](#-key-features)
8. [Installation & Launch](#️-installation--launch)
9. [Environment](#-environment)
10. [Testing Suite](#-testing-suite)
11. [CI Pipeline](#-ci-pipeline)
12. [Documentation](#-documentation)
13. [Non-goals](#-non-goals)
14. [License](#-license)

---

## 🧠 Overview

**I.N.A.Y.A.T.** combines Google Gemini, Mem0 long-term memory, and LlamaIndex `PropertyGraphIndex` over Neo4j AuraDB. It is a **single-agent** RAG system with graceful degradation (RAG → LLM → apology) and per-user document folders.

Upload PDFs or TXT files per profile. Sample documents ship under `data/documents/_samples/` — copy them into `data/documents/{your_name}/` then rebuild the index (see `_samples/README.md`).

The 2026-08-13 remediation (`HOW_TO_FIX.md` §1–§13) is **complete**: docs match the code, CI matches Docker (Python 3.12), user ids are validated, query routing is explicit JSON, graph vis is user-filtered, and observability logs structured query events without prompts or API keys.

---

## 📦 Share this project

Anyone with Docker can run I.N.A.Y.A.T. **Python is not required on the host** if you use Compose.

**Kubernetes is not part of this project.** Kubernetes orchestrates many containers across a cluster (Google/Netflix scale). This repo is one app plus three cloud APIs. **Docker Compose is the share path.** See [DOCKER.md](DOCKER.md).

“Not hardened production” means optional auth and a shared Neo4j database — not “you cannot Docker it.” Native Streamlit on `:8501` and the Docker SPA on `:8000` are the **same agent**; Docker only packages it.

### 1. Clone this branch

```bash
git clone -b august-inayat-v1-new-version-actual-running-to-github https://github.com/Inayat-0007/I.N.A.Y.A.T.-An-agentic-RAG-system-that-remembers-you-reads-your-documents-and-visualises..git
cd I.N.A.Y.A.T.-An-agentic-RAG-system-that-remembers-you-reads-your-documents-and-visualises.
```

### 2. Copy env and add three API keys

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` (never commit it):

| Key | Where to get it |
| --- | ---------------- |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) (**required**) |
| `MEM0_API_KEY` | [Mem0](https://app.mem0.ai/) (recommended) |
| `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` | [Neo4j Aura](https://neo4j.com/cloud/aura/) (recommended) |

Gemini, Mem0, and Aura stay **outside** Docker. Each person uses their own keys.

### 3. Start the SPA

```bash
docker compose up --build
```

Open **http://localhost:8000**. Healthcheck: `GET /api/health`. Uploaded documents land in `./data` on your machine.

Optional Streamlit UI (same backend):

```bash
docker compose --profile streamlit up --build
```

Open **http://localhost:8501**.

### 4. User ids

Workspace names must match `UserId.parse()`: letters, digits, `.` `_` `-` only. **Use underscores, not spaces** (`Moham_Khan`, not `Moham Khan`).

---

## ✨ What this repo now includes

Shipped on branch `august-inayat-v1-new-version-actual-running-to-github` (see [STATUS.md](STATUS.md) for the step checklist):

| Area               | What changed                                                                                                                            |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Docs**           | Canonical README / STATUS / CONTEXT / LICENSE; `WHAT_TO_FIX.md` is historical inventory; examiner one-liner uses **59 smoke / 10 live** |
| **Seed RAG**       | MIT sample PDFs in `data/documents/_samples/` (CEO fact: Dr. Inayat Hussain)                                                            |
| **Config**         | `core/settings.py` (`InayatSettings`); chunk/model from env; overlap must be &lt; chunk size                                            |
| **Identity**       | `core/identity.py` — `UserId.parse()`; charset `[A-Za-z0-9._-]`; **spaces rejected** (use `Moham_Khan`)                                 |
| **Query contract** | `QueryResult` with `route`, `used_memory`, `source_count`; wrapper `query()` still returns `str`                                        |
| **Memory**         | `build_memory_context()` search + get_all, 2000-char cap, fallback if Mem0 is down                                                      |
| **RAG gate**       | Disclaimer/hedge does **not** force LLM fallback when sources exist                                                                     |
| **Ingest**         | PDF `%PDF` + pypdf extract; incremental insert of new files; `INAYAT_SYNC_INGEST=true`; `INAYAT_ALLOW_EMPTY_FROM_EXISTING=false`        |
| **Graph**          | User-filtered vis; `is_mock` + `mock_reason` (`no_documents` vs `offline`); SPA Neural Details drawer |
| **API**            | FastAPI lifespan, CORS from settings, optional `INAYAT_API_KEY` + `X-INAYAT-KEY`, `X-Request-ID`                                        |
| **Demo safety**    | Breaker `forced_open` requires `INAYAT_DEMO_MODE=true` (403 otherwise)                                                                  |
| **Docker**         | Default compose = SPA `:8000` (`Dockerfile.spa`); Streamlit `--profile streamlit` `:8501`                                               |
| **Flags**          | MMR off by default; async ingest off by default (sync wait-for-200)                                                                     |
| **Observability**  | `core/observability.py` — `event=query user_id=... route=... latency_ms=... source_count=... mem0_ok=... neo4j_ok=...`                  |
| **SPA**            | Badges from API `route` / `used_memory` (not inferred from answer text); mock-graph banner; 403 copy for demo mode                      |
| **Tests**          | 59 smoke (no keys required for new identity/settings/route tests) + `tests/test_api_contract.py` + live CEO skipUnless                  |

---

## 🔁 System Architecture

```mermaid
flowchart TD
    User([User Profile]) -->|Query / Upload| UI[Streamlit app.py or React + api.py]
    UI --> Agent[query_detailed]
    Agent --> Mem0[Mem0 Cloud]
    Agent --> Neo4j[Neo4j PropertyGraphIndex]
    Agent --> LLM[Gemini Flash Lite]
    Agent -->|route rag llm apology| UI
    Health[Health and circuit breakers] --> Mem0
    Health --> Neo4j
    Health --> LLM
```

Degradation order: **RAG** (sources present) → **LLM** (no sources / RAG failed) → **apology** (LLM also failed). Circuit breakers isolate Mem0 and Neo4j failures so the process stays up.

---

## ⚙️ Tech Stack

Pinned versions are in [constraints.txt](constraints.txt).

| Component         | Technology             | Pinned version             | Purpose                   |
| :---------------- | :--------------------- | :------------------------- | :------------------------ |
| **UI (legacy)**   | Streamlit              | `1.58.0`                   | Demo dashboard (`app.py`) |
| **UI (modern)**   | React + Vite + FastAPI | see `frontend/`            | SPA + REST API            |
| **Graph store**   | Neo4j AuraDB           | driver `5.28.4`            | Property graph storage    |
| **Memory**        | Mem0                   | `mem0ai==2.0.4`            | Persistent user memory    |
| **LLM**           | Gemini Flash Lite      | `gemini-flash-lite-latest` | Generation                |
| **Embeddings**    | Gemini                 | `gemini-embedding-001`     | 3072-dim vectors          |
| **RAG**           | LlamaIndex             | core `0.14.22`             | PropertyGraphIndex        |
| **Visualization** | Vis.js                 | in frontend                | Graph drawer              |
| **Config**        | pydantic-settings      | `2.12.0`                   | Typed env settings        |

---

## 📂 Project Structure

```
INAYAT/
├── app.py                        # Streamlit UI (--profile streamlit)
├── api.py                        # FastAPI REST + SPA static host (:8000)
├── run_spa.py                    # Dev: uvicorn + Vite
├── warmup.py                     # Neo4j RETURN 1; optional default index
├── activate.ps1                  # Windows launcher (sets INAYAT_DEMO_MODE)
├── requirements.txt
├── constraints.txt               # Pinned dependency versions
├── .env.example                  # Copy to .env (never commit secrets)
├── DOCKER.md                     # Compose share path; why k8s is not used
├── LICENSE                       # MIT
├── STATUS.md                     # One-page examiner status
├── CONTEXT.md                    # Contributor module map
├── WHAT_TO_FIX.md                # Historical issue inventory
├── HOW_TO_FIX.md                 # Remediation spec (implemented)
├── core/
│   ├── settings.py               # Typed env (InayatSettings)
│   ├── identity.py               # UserId.parse()
│   ├── observability.py          # request_id + event=query logs
│   ├── schemas.py                # QueryInput / QueryResult
│   ├── conversation.py           # Short-term chat buffer
│   ├── ingest.py                 # Uploads + index lifecycle
│   ├── agent.py                  # query_detailed() + query() → str
│   ├── llm_setup.py              # Gemini LLM + embeddings
│   ├── memory.py                 # Mem0 + build_memory_context()
│   ├── graph_store.py            # Neo4j + user-filtered vis JSON
│   ├── resilience.py             # Circuit breakers + demo gate
│   ├── health.py                 # HealthMonitor
│   ├── startup.py                # Boot validation
│   ├── compat.py                 # Backwards-compat exports
│   └── logging_config.py         # Rotating file + console
├── frontend/                     # React SPA (Vite)
├── data/documents/_samples/      # MIT sample PDFs
├── tests/
│   ├── smoke_test.py             # 59 tests (CI)
│   ├── test_api_contract.py      # FastAPI TestClient (loaded by smoke)
│   └── backend_feature_test.py   # 10 live integration tests
├── scripts/
│   └── browser_e2e.py            # Optional Playwright E2E vs Streamlit :8501
├── .github/workflows/
│   ├── ci.yml                    # Python 3.12 + pip-audit + smoke + frontend-build
│   └── integration.yml           # Weekly / manual live tests
├── Dockerfile                    # Streamlit :8501
├── Dockerfile.spa                # Multi-stage Vite + uvicorn :8000
├── .dockerignore
└── docker-compose.yml            # Default SPA :8000; --profile streamlit :8501
```

---

## ✨ Key Features

- **Isolated user sessions** — `data/documents/{user_id}/` + Mem0 `user_id` + metadata filters on a **shared Neo4j database** (not per-user Aura instances). Isolation is demo-grade metadata, not multi-tenant SaaS.
- **Validated user ids** — `UserId.parse()`; letters, digits, `.` `_` `-` only. **Use underscores, not spaces** (`Moham_Khan`). Path tricks (`../etc`, `alice/bob`) return HTTP 400.
- **Property-graph RAG** — LlamaIndex `PropertyGraphIndex` over Neo4j. There is **no separate BM25 index**.
- **Explicit routes** — SPA badges use `route` (`rag` / `llm` / `apology`) and `used_memory` from `/api/query`, not answer-text heuristics.
- **MMR retrieval** — off by default (`INAYAT_MMR_ENABLED=false`); falls back to `similarity_top_k` if LlamaIndex rejects MMR kwargs.
- **Chunking** — `INAYAT_CHUNK_SIZE` / `INAYAT_CHUNK_OVERLAP` (defaults 512/64). Rebuild the index after changing chunk settings.
- **Empty-folder isolation** — `INAYAT_ALLOW_EMPTY_FROM_EXISTING=false` by default (no shared-graph attach).
- **Ingest** — PDF magic-byte check + pypdf text extract; new files are inserted incrementally (full rebuild only when needed). Streamlit stays sync. `POST /api/upload` waits for 200 when `INAYAT_SYNC_INGEST=true` (default).
- **Dual UI** — Streamlit (`:8501`) for demos; FastAPI+React SPA (`:8000`) is the Docker default. Graph overlay: empty vs offline `is_mock` banners and Neural Details.
- **Circuit breakers** — Mem0/Neo4j degradation without crashes. Toggles need `INAYAT_DEMO_MODE=true`.
- **Optional API key** — empty `INAYAT_API_KEY` keeps the open demo; if set, mutating `/api/*` routes require `X-INAYAT-KEY`.
- **Observability** — UUID `X-Request-ID` per HTTP request and Streamlit turn; structured query logs; no full prompts or keys.

---

## 🛠️ Installation & Launch

Prefer **[Share this project](#-share-this-project)** if you only want to run the app. Copy `.env.example` → `.env` and set `GEMINI_API_KEY` (required). Workspace ids must match `UserId` rules (underscores, not spaces).

### Option A: Native Windows (Streamlit demo)

```powershell
powershell -ExecutionPolicy Bypass -File activate.ps1
```

Sets `INAYAT_DEMO_MODE=true`, runs warmup, launches Streamlit at `http://localhost:8501`.

Copy samples into your profile folder first:

```powershell
Copy-Item -Recurse "data\documents\_samples\*" "data\documents\YourName\"
```

### Option B: Docker Compose (default = SPA on :8000)

Same commands as [Share this project](#-share-this-project). Full notes: [DOCKER.md](DOCKER.md).

```bash
docker compose up --build
```

Serves FastAPI + built React at `http://localhost:8000`. Healthcheck: `GET /api/health`. Volume: `./data`. No Kubernetes.

Streamlit profile (functionally the same agent as native `:8501`):

```bash
docker compose --profile streamlit up --build
```

Optional `INAYAT_API_KEY` gates mutating `/api/*` routes via `X-INAYAT-KEY`.

### Option C: FastAPI + React dev

```bash
pip install -r requirements.txt -c constraints.txt
python run_spa.py
```

API on `:8000`, Vite on `:5173`.

---

## 🔐 Environment

| Variable                           | Required        | Notes                       |
| ---------------------------------- | --------------- | --------------------------- |
| `GEMINI_API_KEY`                   | **Yes**         | Generation + embeddings     |
| `MEM0_API_KEY`                     | Recommended     | Memory degrades if missing  |
| `NEO4J_URI` / `NEO4J_PASSWORD`     | Recommended     | Graph degrades if missing   |
| `NEO4J_USERNAME`                   | Default `neo4j` |                             |
| `INAYAT_DEMO_MODE`                 | Demo toggles    | `true` for breaker UI       |
| `INAYAT_API_KEY`                   | Optional        | If set, send `X-INAYAT-KEY` |
| `INAYAT_CORS_ORIGINS`              | Optional        | Explicit allow-list         |
| `INAYAT_MMR_ENABLED`               | Default `false` |                             |
| `INAYAT_SYNC_INGEST`               | Default `true`  | `false` → 202 + poll        |
| `INAYAT_ALLOW_EMPTY_FROM_EXISTING` | Default `false` | Safer empty folders         |

See `.env.example` for chunk size, top_k, log level, and memory context cap.

---

## 🧪 Testing Suite

```bash
# CI smoke suite (59 tests) — no live keys required for identity/settings/route tests
python tests/smoke_test.py

# Live integration (10 tests — requires real API keys)
python tests/backend_feature_test.py
```

Do **not** use pytest for CI; the supported runner is `python tests/smoke_test.py`. The smoke `__main__` also loads `tests/test_api_contract.py` (invalid `user_id` → 400, breaker toggle without demo → 403, CORS, `X-Request-ID`).

Live RAG CEO assertion is skipped unless documents exist under a profile folder; after copying `_samples/`, the CEO fact remains asserted.

---

## 🔄 CI Pipeline

On push/PR to `main` or `master` (see [.github/workflows/ci.yml](.github/workflows/ci.yml)):

1. **flake8** — critical errors only (`E9,F63,F7,F82`)
2. **black** — formatting check
3. **gitleaks** — secret scan
4. **pip-audit** — dependency vulnerability scan
5. **smoke tests** — `python tests/smoke_test.py` (59 tests)

**frontend-build** job (parallel): `npm ci` + `npm run build` in `frontend/`.

Does **not** run on every PR: `backend_feature_test.py` (live keys). See [.github/workflows/integration.yml](.github/workflows/integration.yml) — weekly schedule + manual dispatch. **Cost:** live Gemini + Mem0 + Neo4j per run.

Python **3.12**, installs with `pip install -r requirements.txt -c constraints.txt`.

**GitHub Actions note:** `ci.yml` and `integration.yml` live in this repo. If a push is rejected because the token cannot update workflow files (`workflows` scope), paste the YAML in the GitHub UI (Actions → New workflow) or push with a PAT that includes `workflow`. The rest of the branch still ships without that permission.

---

## 📄 Documentation

| File                                                       | Role                                               |
| ---------------------------------------------------------- | -------------------------------------------------- |
| [README.md](README.md)                                     | This file — install, architecture, canonical facts |
| [DOCKER.md](DOCKER.md)                                     | Compose share path; Kubernetes is not required     |
| [STATUS.md](STATUS.md)                                     | One-page examiner sheet + completed §10 order      |
| [CONTEXT.md](CONTEXT.md)                                   | Contributor module map                             |
| [WHAT_TO_FIX.md](WHAT_TO_FIX.md)                           | Issue inventory (superseded for counts)            |
| [HOW_TO_FIX.md](HOW_TO_FIX.md)                             | Remediation spec (implemented §1–§13)              |
| [MASTER_DEEP_DIVE_REPORT.txt](MASTER_DEEP_DIVE_REPORT.txt) | Historical audit (superseded for counts)           |
| [demo_script.md](demo_script.md)                           | Live presentation script                           |

---

## 🚫 Non-goals

Not in this product: Kubernetes/cluster manifests, LangGraph/CrewAI multi-agent orchestration, per-user Neo4j Aura instances, replacing Mem0 or Neo4j, rewriting Streamlit into React in one commit, or calling optional `INAYAT_API_KEY` “production hardening.” Sharing is **Docker Compose**, not k8s.

---

## 📜 License

MIT License — see [LICENSE](LICENSE).
