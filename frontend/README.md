# I.N.A.Y.A.T. React SPA

Vite + React + Tailwind + Framer Motion + Vis.js workspace. This is the **modern web UI**, served by FastAPI (`api.py`) on port **8000**. Streamlit (`app.py` on **8501**) remains the demo dashboard — this SPA does not replace it.

Python for the API is **3.12** (same as Docker / CI). Node **20+** for the frontend toolchain.

## Architecture

```
[ React + Vite SPA ]  -- REST / JSON / multipart -->  [ FastAPI api.py ]
                                                         |
                                              core.agent / memory / ingest / graph
                                                         |
                                              Gemini + Mem0 + Neo4j AuraDB
```

Production: FastAPI serves `frontend/dist/` (see `Dockerfile.spa`). Dev: `python run_spa.py` (API `:8000`, Vite `:5173` with proxy).

## API (high level)

| Method | Path | Notes |
| ------ | ---- | ----- |
| GET | `/api/startup` | Boot warnings |
| GET | `/api/health` | Gemini / Mem0 / Neo4j + breakers |
| POST | `/api/health/toggle` | Demo breakers; **403** unless `INAYAT_DEMO_MODE=true` |
| GET | `/api/memories` | Mem0 pills for `user_id` |
| POST | `/api/memories/clear` | Clear Mem0 for `user_id` |
| GET | `/api/graph` | Vis.js payload; `is_mock` + `mock_reason` (`empty` / `offline`) |
| POST | `/api/query` | Returns `route`, `used_memory`, `source_count` (SPA badges use these fields) |
| POST | `/api/upload` | PDF/TXT; sync 200 by default, or 202 + poll `/api/index-status` |

If `INAYAT_API_KEY` is set, mutating routes need `X-INAYAT-KEY` (`VITE_INAYAT_API_KEY` via `apiHeaders.js`).

**User ids:** same rules as `core/identity.py` — start with alphanumeric; only `.` `_` `-`; **underscores, not spaces**.

## Run

```bash
pip install -r requirements.txt -c constraints.txt
cd frontend && npm install && cd ..
python run_spa.py
```

Open http://localhost:5173. Production-style: `npm run build` then serve via `python api.py` on http://localhost:8000.

## Components

| File | Role |
| ---- | ---- |
| `App.jsx` | Landing vs workspace; `?user=` session |
| `LandingPage.jsx` | Gateway + 59-test stat |
| `ArchitectureDiagram.jsx` | Pipeline SVG + demo breakers |
| `FeaturesShowcase.jsx` | Capability cards |
| `AgentWorkspace.jsx` | Chat, ingest, health, graph + Neural Details |
| `ProductTour.jsx` | Short demo walkthrough |
| `apiHeaders.js` | Optional `X-INAYAT-KEY` |
| `userId.js` | Client-side `UserId` validation |
