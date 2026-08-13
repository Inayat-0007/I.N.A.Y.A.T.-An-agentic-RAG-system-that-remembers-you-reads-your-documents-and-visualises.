# I.N.A.Y.A.T. — CONTEXT.md (Contributor Map)

> **Note:** Canonical facts and test counts live in [README.md](README.md) and [STATUS.md](STATUS.md).
> This file maps modules for contributors and AI assistants.

---

## Project identity

| Field        | Value                                                         |
| ------------ | ------------------------------------------------------------- |
| **Name**     | Intelligent Neural Architecture for Yielding Agentic Thinking |
| **Model**    | Single-agent RAG (not multi-agent orchestration)              |
| **Python**   | 3.12                                                          |
| **Maturity** | Advanced MVP / demo-ready                                     |

---

## Technology stack

| Layer      | Tool                                      | Notes                                                          |
| ---------- | ----------------------------------------- | -------------------------------------------------------------- |
| LLM        | `gemini-flash-lite-latest`                | via `core/llm_setup.py`                                        |
| Embeddings | `gemini-embedding-001`                    | 3072-dim                                                       |
| Memory     | Mem0 (`mem0ai==2.0.4`)                    | `core/memory.py`                                               |
| Graph      | Neo4j Aura (`neo4j==5.28.4`)              | `core/graph_store.py`                                          |
| RAG        | LlamaIndex PropertyGraphIndex (`0.14.22`) | `core/ingest.py`, `core/agent.py`                              |
| UI         | Streamlit `1.58.0` + React SPA            | `app.py`, `api.py`, `frontend/`                                |
| Config     | pydantic-settings                         | `core/settings.py`                                             |
| CI         | GitHub Actions                            | flake8 + black + gitleaks + pip-audit + smoke + frontend build |

---

## Module map (`core/`)

| Module              | Responsibility                                    |
| ------------------- | ------------------------------------------------- |
| `settings.py`       | Typed env (`InayatSettings`)                      |
| `identity.py`       | `UserId.parse()` — no spaces; `_` `.` `-` ok      |
| `observability.py`  | `request_id`, `log_query_event()`, `trace_span()` |
| `schemas.py`        | `QueryInput`, `QueryResult`                       |
| `conversation.py`   | In-memory short-term turns                        |
| `ingest.py`         | Uploads, pypdf extract, incremental index build   |
| `agent.py`          | `query_detailed()`, legacy `query()` → str        |
| `llm_setup.py`      | Gemini LLM + embeddings only                      |
| `memory.py`         | Mem0 CRUD (no chat history)                       |
| `graph_store.py`    | Neo4j driver, vis JSON                            |
| `resilience.py`     | CircuitBreaker, `set_breaker_forced_open()`       |
| `health.py`         | `HealthMonitor`                                   |
| `startup.py`        | `run_startup()`, `enforce_critical_env_or_exit()` |
| `compat.py`         | Backwards-compat re-exports                       |
| `logging_config.py` | File + console logging                            |

---

## Entry points

| File           | Role                                                    |
| -------------- | ------------------------------------------------------- |
| `app.py`       | Streamlit UI (`--profile streamlit`)                    |
| `api.py`       | FastAPI REST + `frontend/dist` (Docker default `:8000`) |
| `run_spa.py`   | Local dual-server dev                                   |
| `warmup.py`    | Neo4j keepalive + health                                |
| `activate.ps1` | Windows launcher                                        |

---

## Tests

| File                            | Count | CI             |
| ------------------------------- | ----- | -------------- |
| `tests/smoke_test.py`           | 59    | Yes            |
| `tests/backend_feature_test.py` | 10    | No (live keys) |

Run smoke: `python tests/smoke_test.py`

---

## CI pipeline (actual)

On push/PR to `main` or `master` ([ci.yml](.github/workflows/ci.yml)):

1. flake8 (E9,F63,F7,F82)
2. black --check
3. gitleaks
4. pip-audit (`pip install pip-audit` then `pip-audit -r requirements.txt`)
5. `python tests/smoke_test.py` (59 tests)

Parallel job **frontend-build**: `npm ci` + `npm run build` in `frontend/`.

Live integration ([integration.yml](.github/workflows/integration.yml)): `workflow_dispatch` + weekly cron; runs `backend_feature_test.py` (costs Gemini + Mem0 + Neo4j).

Python 3.12. Installs with `-c constraints.txt`. No pytest. No Safety package.

---

## Environment

| Variable                      | Required                                                  |
| ----------------------------- | --------------------------------------------------------- |
| `GEMINI_API_KEY`              | **Yes**                                                   |
| `MEM0_API_KEY`                | Recommended                                               |
| `NEO4J_URI`, `NEO4J_PASSWORD` | Recommended                                               |
| `NEO4J_USERNAME`              | Default `neo4j`                                           |
| `INAYAT_DEMO_MODE`            | For circuit-breaker demo toggles                          |
| `INAYAT_API_KEY`              | Optional; if set, mutating API routes need `X-INAYAT-KEY` |

Shared Neo4j database + `user_id` metadata (not per-user Aura DBs). Workspace ids: letters, digits, `.` `_` `-` — **underscores, not spaces**.

See `.env.example` for `INAYAT_*` tuning keys.

---

## Data

- Sample docs: `data/documents/_samples/` (MIT) — copy into `data/documents/{profile_name}/`
- `data/documents/.gitkeep` keeps the tree in git

---

## Related docs

- [WHAT_TO_FIX.md](WHAT_TO_FIX.md) — issue inventory
- [HOW_TO_FIX.md](HOW_TO_FIX.md) — remediation spec (§10 order complete; see STATUS.md)
- [MASTER_DEEP_DIVE_REPORT.txt](MASTER_DEEP_DIVE_REPORT.txt) — historical (superseded for counts)

## Non-goals

LangGraph/CrewAI, per-user Aura DBs, Mem0/Neo4j replacement, Streamlit→React rewrite in one commit, production-hardening claims while auth is optional.
