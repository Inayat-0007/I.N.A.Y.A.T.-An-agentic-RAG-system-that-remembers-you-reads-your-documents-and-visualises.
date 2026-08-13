# I.N.A.Y.A.T. — Current Status (Examiner Sheet)

**Last updated:** 2026-08-13  
**Maturity:** Advanced MVP / demo-ready — not hardened production.

## Examiner one-liner

I.N.A.Y.A.T. is a **single-agent, production-pattern RAG system** (Gemini + LlamaIndex PropertyGraphIndex + Neo4j + Mem0) with **documented** dual UIs (Streamlit `:8501` + React SPA `:8000`), **typed** config, **validated** user ids (**underscores, not spaces**), incremental PDF ingest, **CI that matches Docker (Python 3.12)**, and **honest** test counts (**59 smoke** on every PR, **10 live** on schedule). Isolation is **soft multi-tenancy** on a shared graph, which is acceptable for a demo and explicitly not a multi-tenant SaaS.

## Canonical facts

| Fact                 | Value                                                                                     |
| -------------------- | ----------------------------------------------------------------------------------------- |
| **Agent model**      | Single-agent RAG pipeline (not LangGraph/CrewAI multi-agent)                              |
| **Python**           | 3.12 (Docker); CI targets 3.12                                                            |
| **LLM**              | `gemini-flash-lite-latest`                                                                |
| **Embeddings**       | `gemini-embedding-001` (3072-dim)                                                         |
| **Chunking**         | size 512, overlap 64 (`INAYAT_CHUNK_SIZE` / `INAYAT_CHUNK_OVERLAP`)                       |
| **Retrieval**        | PropertyGraphIndex, `similarity_top_k=5`, `user_id` metadata filter                       |
| **Smoke tests**      | 59 (`tests/smoke_test.py`) — run on every CI push                                         |
| **Live integration** | 10 (`tests/backend_feature_test.py`) — manual / scheduled only                            |
| **CI**               | flake8 + black + gitleaks + pip-audit + smoke + frontend build                            |
| **Docker**           | Default SPA `Dockerfile.spa` `:8000`; Streamlit `--profile streamlit` `:8501`             |
| **Seed docs**        | `data/documents/_samples/` — copy to `{your_name}/`                                       |
| **UIs**              | Streamlit (`app.py`) + FastAPI/React (`api.py`, `frontend/`)                              |
| **Isolation**        | Soft: folders + metadata + Mem0 `user_id`; **shared Neo4j DB**; optional `INAYAT_API_KEY` |
| **Critical env**     | `GEMINI_API_KEY`                                                                          |
| **Recommended env**  | `MEM0_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`                           |
| **User ids**         | `UserId.parse()` — no spaces; use `Moham_Khan`                                            |
| **Ingest**           | pypdf extract + incremental insert; sync default                                          |
| **Demo breakers**    | `INAYAT_DEMO_MODE=true` (set by `activate.ps1`)                                           |

## How to run

```powershell
powershell -ExecutionPolicy Bypass -File activate.ps1
```

Upload PDFs per user under `data/documents/{profile_name}/`. Copy MIT samples from `data/documents/_samples/` first if you want a quick RAG demo (CEO fact in `inayat_company_facts.pdf`).

## Doc map

| File                          | Role                                        |
| ----------------------------- | ------------------------------------------- |
| `README.md`                   | Install, architecture, canonical facts      |
| `CONTEXT.md`                  | Contributor module map                      |
| `WHAT_TO_FIX.md`              | Issue inventory                             |
| `HOW_TO_FIX.md`               | Remediation spec                            |
| `MASTER_DEEP_DIVE_REPORT.txt` | Historical snapshot (superseded for counts) |
| `STATUS.md`                   | This sheet                                  |

## Remediation order (`HOW_TO_FIX.md` §10) — complete

Each step left the app bootable. Multi-agent LangGraph was not started.

| Step | Work | Status |
| ---- | ---- | ------ |
| 1 | Canonical docs + LICENSE + STATUS | Done |
| 2 | Seed PDFs under `data/documents/_samples/` + live `skipUnless` | Done |
| 3 | CI Python 3.12 + constraints + frontend-build + pip-audit | Done |
| 4 | `core/settings.py` wired into `llm_setup` | Done (defaults unchanged) |
| 5 | `core/identity.py` on paths and API `user_id` | Done |
| 6 | `QueryResult` + `query()` str wrapper + SPA badges | Done |
| 7 | Mem0 search on hot path with fallback | Done |
| 8 | Graph vis Cypher user filter | Done |
| 9 | FastAPI lifespan, CORS origins, `INAYAT_DEMO_MODE` gate | Done |
| 10 | Optional `INAYAT_API_KEY` (off by default) | Done |
| 11 | Compose SPA default + `Dockerfile.spa`; Streamlit `--profile streamlit` | Done (Phase 2 flip) |
| 12 | MMR + async ingest flags (off / sync-default) | Done |
| 13 | Observability `event=query` logs | Done |

Punch-list mapping (`WHAT_TO_FIX.md` → spec): 1–14 → §1; 15–21 → §2/§9; 22–25 → §3; 26–34 → §4; 35–42 → §3.2/§5/§6; 43–46 → §6.3; 47–48 → §7; keep-list E → §0.3.

## Non-goals (out of scope)

- Rewriting Streamlit into React in one commit (both UIs remain)
- Per-user Neo4j Aura instances
- LangGraph / CrewAI multi-agent orchestration
- Replacing Mem0 or Neo4j
- Claiming production hardening while auth is optional
- Incomplete snippets or `# TODO` in shipped code
