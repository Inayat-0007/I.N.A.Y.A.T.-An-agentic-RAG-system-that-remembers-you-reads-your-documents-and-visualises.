# I.N.A.Y.A.T. — Current Status (Examiner Sheet)

**Last updated:** 2026-08-13  
**Maturity:** Advanced MVP / demo-ready — not hardened production.

## Canonical facts

| Fact                 | Value                                                                                     |
| -------------------- | ----------------------------------------------------------------------------------------- |
| **Agent model**      | Single-agent RAG pipeline (not LangGraph/CrewAI multi-agent)                              |
| **Python**           | 3.12 (Docker); CI targets 3.12                                                            |
| **LLM**              | `gemini-flash-lite-latest`                                                                |
| **Embeddings**       | `gemini-embedding-001` (3072-dim)                                                         |
| **Chunking**         | size 512, overlap 64 (`INAYAT_CHUNK_SIZE` / `INAYAT_CHUNK_OVERLAP`)                       |
| **Retrieval**        | PropertyGraphIndex, `similarity_top_k=5`, `user_id` metadata filter                       |
| **Smoke tests**      | 52 (`tests/smoke_test.py`) — run on every CI push                                         |
| **Live integration** | 10 (`tests/backend_feature_test.py`) — manual / scheduled only                            |
| **CI**               | flake8 + black + gitleaks + pip-audit + smoke + frontend build                            |
| **Docker**           | Default SPA `Dockerfile.spa` `:8000`; Streamlit `--profile streamlit` `:8501`             |
| **Seed docs**        | `data/documents/_samples/` — copy to `{your_name}/`                                       |
| **UIs**              | Streamlit (`app.py`) + FastAPI/React (`api.py`, `frontend/`)                              |
| **Isolation**        | Soft: folders + metadata + Mem0 `user_id`; **shared Neo4j DB**; optional `INAYAT_API_KEY` |
| **Critical env**     | `GEMINI_API_KEY`                                                                          |
| **Recommended env**  | `MEM0_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`                           |
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
