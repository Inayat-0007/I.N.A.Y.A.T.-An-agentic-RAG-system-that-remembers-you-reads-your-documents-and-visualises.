# I.N.A.Y.A.T. — React & FastAPI SPA Frontend Integration

This subproject implements a cinematic, futuristic single-page application (SPA) built using **React + Vite + Tailwind CSS + Framer Motion + Vis.js**, backed by a resilient **FastAPI** REST server. It replaces the original Streamlit frontend (`app.py`) with a highly interactive, 2026-style cognitive AI workspace.

---

## 🏗️ Architecture Overview

The system operates on an isolated REST framework:

```
[ React + Vite SPA ]  <--- (REST API / JSON / Multipart) --->  [ FastAPI Server (api.py) ]
                                                                       |
                                                           [ core.agent / core.memory ]
                                                                       |
                                                           [ Neo4j AuraDB & Mem0 Cloud ]
```

1.  **FastAPI (`api.py`)**: Imports the core Python modules (`core.agent`, `core.memory`, `core.graph_store`, `core.health`, `core.startup`) and exposes them as lightweight REST endpoints. It also serves the compiled React production static files from `frontend/dist/`.
2.  **React Frontend (`frontend/`)**: Manages isolated user workspaces, dynamic routing query strings, real-time file uploading, and custom SVG sequence animations. Contains a full-canvas Vis.js knowledge graph.

---

## 🔌 API Endpoints Reference

The FastAPI server exposes the following endpoints:

*   `GET /api/startup`: Retrieves boot warnings and config checks.
*   `GET /api/health`: Fetches connectivity states for Gemini, Mem0, and Neo4j, plus active circuit breaker parameters.
*   `POST /api/health/toggle`: Force blows breakers (`mem0` or `neo4j`) for resilience simulation.
*   `GET /api/memories?user_id=...`: Retrieves memory pills list from Mem0.
*   `POST /api/memories/clear?user_id=...`: Deletes memories.
*   `GET /api/graph?user_id=...`: Queries database entity relations, returning Vis.js node/edge objects.
*   `POST /api/query`: Submits natural language queries. Enforces the 6-step loop: memory update -> RAG retrieval -> LLM execution -> callback check.
*   `POST /api/upload`: Multi-file form uploader. Automatically isolatively stores documents to `data/documents/{user_id}/` and rebuilds the LlamaIndex PropertyGraph index.

---

## 🚀 Running the App

### 1. Requirements
Ensure you have the following installed:
*   **Python 3.10+**
*   **Node.js v20+** and **npm**

### 2. Install dependencies
From the project root directory, install python REST dependencies:
```bash
pip install fastapi uvicorn python-multipart
```

And install React node modules:
```bash
cd frontend
npm install
cd ..
```

### 3. Run in Development Mode
To run both the backend FastAPI service (port 8000) and the Vite frontend dev server (port 5173) with automatic proxying in parallel:
```bash
python run_spa.py
```
Open **http://localhost:5173** in your browser.

### 4. Build and Run in Production Mode
Compile the React code to static assets and serve them directly from FastAPI:
```bash
cd frontend
npm run build
cd ..
python api.py
```
Open **http://localhost:8000** in your browser.

---

## 🎨 UI/UX Component Blueprint

All visual components are modularly organized inside `frontend/src/components/`:

*   [App.jsx](file:///c:/Users/moham/Music/INAYAT/frontend/src/App.jsx): Controls routing states, session login query parameters, and critical startup gating.
*   [LandingPage.jsx](file:///c:/Users/moham/Music/INAYAT/frontend/src/components/LandingPage.jsx): Implements the full-screen canvas particle network and profile portal.
*   [ArchitectureDiagram.jsx](file:///c:/Users/moham/Music/INAYAT/frontend/src/components/ArchitectureDiagram.jsx): An interactive SVG loop with glassmorphic tooltip drawers and electrical spark breakers.
*   [FeaturesShowcase.jsx](file:///c:/Users/moham/Music/INAYAT/frontend/src/components/FeaturesShowcase.jsx): Grid containing frosted glass hover cards.
*   [AgentWorkspace.jsx](file:///c:/Users/moham/Music/INAYAT/frontend/src/components/AgentWorkspace.jsx): Contains the primary layout (Collapsible profile lists, chat citations, upload fields, and Vis.js panels).
*   [ProductTour.jsx](file:///c:/Users/moham/Music/INAYAT/frontend/src/components/ProductTour.jsx): SaaS walkthrough overlay.
