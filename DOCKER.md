# Docker for I.N.A.Y.A.T.

This project is **Docker Compose ready**. You do **not** need Kubernetes.

## Why not Kubernetes?

**Kubernetes (k8s)** is a cluster orchestrator. It schedules *many* containers across *many* machines (the kind of setup Google or Netflix use). I.N.A.Y.A.T. is a **single-app demo**: one container talks to three **cloud APIs** you already have accounts for.

| Tool | What it does here |
| ---- | ----------------- |
| **Docker Compose** | Builds and runs this app on your laptop or a shared machine. **This is the share path.** |
| **Kubernetes** | Not used. No cluster, no manifests, no Helm. Skip it. |

“Not hardened production” in the README means: optional API key, shared Neo4j database, demo-grade isolation. It does **not** mean “you cannot run or share it.” Compose packages the same app that already runs natively.

## One-command share path (SPA)

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose). **Python is not required on the host.**

```bash
git clone -b august-inayat-v1-new-version-actual-running-to-github https://github.com/Inayat-0007/I.N.A.Y.A.T.-An-agentic-RAG-system-that-remembers-you-reads-your-documents-and-visualises..git
cd I.N.A.Y.A.T.-An-agentic-RAG-system-that-remembers-you-reads-your-documents-and-visualises.
copy .env.example .env
# then edit .env and paste your three keys (see README)

docker compose up --build
```

On macOS/Linux use `cp .env.example .env` instead of `copy`.

Open **http://localhost:8000**. Health: **GET http://localhost:8000/api/health**.

Documents persist in `./data` (bind-mounted to `/app/data`).

## Streamlit (same backend, other UI)

Native Streamlit on `:8501` is the same RAG agent. Docker packages that UI too:

```bash
docker compose --profile streamlit up --build
```

Open **http://localhost:8501**.

## What stays *outside* Docker

Gemini, Mem0, and Neo4j Aura are **cloud services**. The container does not host them. Each user copies `.env.example` → `.env` and brings **their own keys**. Never commit `.env`.

## Images

| File | Role |
| ---- | ---- |
| `Dockerfile.spa` | Default. Node 20 builds the React SPA, then Python 3.12 runs `uvicorn api:app` on `:8000`. |
| `Dockerfile` | Streamlit `app.py` on `:8501` (`--profile streamlit`). |
| `docker-compose.yml` | SPA service by default; `./data` volume; `.env` injected at **runtime** (not baked into the image). |
