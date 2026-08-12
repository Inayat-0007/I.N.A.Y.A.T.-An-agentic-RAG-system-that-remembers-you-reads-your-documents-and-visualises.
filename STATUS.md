# I.N.A.Y.A.T. — Current Status (Examiner Sheet)

**Last updated:** 2026-08-13  
**Maturity:** Advanced MVP / demo-ready — not hardened production.

## Canonical facts

| Fact | Value |
|------|-------|
| **Agent model** | Single-agent RAG pipeline (not LangGraph/CrewAI multi-agent) |
| **Python** | 3.12 (Docker); CI targets 3.12 |
| **LLM** | `gemini-flash-lite-latest` |
| **Embeddings** | `gemini-embedding-001` (3072-dim) |
| **Chunking** | size 512, overlap 64 (`INAYAT_CHUNK_SIZE` / `INAYAT_CHUNK_OVERLAP`) |
| **Retrieval** | PropertyGraphIndex, `similarity_top_k=5`, `user_id` metadata filter |
| **Smoke tests** | 36 (`tests/smoke_test.py`) — run on every CI push |
| **Live integration** | 10 (`tests/backend_feature_test.py`) — manual / scheduled only |
| **CI** | flake8 (E9,F63,F7,F82) + black + gitleaks + smoke tests |
| **Docker** | `python:3.12-slim`, Streamlit `:8501`, single-container compose |
| **Seed docs** | None in git — only `data/documents/.gitkeep` |
| **UIs** | Streamlit (`app.py`) + FastAPI/React (`api.py`, `frontend/`) |
| **Isolation** | Soft: per-user folders + metadata + Mem0 `user_id`; shared Neo4j DB; no auth |
| **Critical env** | `GEMINI_API_KEY` |
| **Recommended env** | `MEM0_API_KEY`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` |
| **Demo breakers** | `INAYAT_DEMO_MODE=true` (set by `activate.ps1`) |

## How to run

```powershell
powershell -ExecutionPolicy Bypass -File activate.ps1
```

Upload PDFs per user under `data/documents/{profile_name}/` — the repo does not ship scenario PDFs.

## Doc map

| File | Role |
|------|------|
| `README.md` | Install, architecture, canonical facts |
| `CONTEXT.md` | Contributor module map |
| `WHAT_TO_FIX.md` | Issue inventory |
| `HOW_TO_FIX.md` | Remediation spec |
| `MASTER_DEEP_DIVE_REPORT.txt` | Historical snapshot (superseded for counts) |
| `STATUS.md` | This sheet |
