# I.N.A.Y.A.T. — Master Demo & Presentation Script (2026)

This document is your reference guide for presenting the project to examiners or advisors. Follow these steps to demonstrate every architectural innovation.

---

## ⚡ Step 1: Pre-Demo Preparation

1. **API Keys**: Make sure your `.env` file contains valid API keys for Gemini, Mem0, and Neo4j.
2. **Demo mode**: Set `INAYAT_DEMO_MODE=true` in `.env` (or use `activate.ps1`, which enables it) so Scene 5 circuit-breaker toggles work in the sidebar.
3. **Neo4j Status**: Check that your Neo4j AuraDB instance is running (not paused).
4. **Documents**: Copy MIT samples from `data/documents/_samples/` into `data/documents/{YourName}/` (CEO fact lives in `inayat_company_facts.pdf`). You can also add your own PDFs. Circuit-breaker Scene 5 needs `INAYAT_DEMO_MODE=true`.
5. **SPA alternative**: `docker compose up --build` serves the React UI at `http://localhost:8000` (default). Streamlit remains `activate.ps1` or `docker compose --profile streamlit up`.

---

## 🚀 Step 2: Launch the System

Open a PowerShell terminal in the project root and run:

```powershell
powershell -ExecutionPolicy Bypass -File activate.ps1
```

**What this demonstrates to the examiner:**

- Automates virtual environment setup and cross-platform wheel compatibility.
- Runs `warmup.py` to check service connectivity before booting.
- Boots Streamlit and pre-warms/pre-builds the `PropertyGraphIndex` from files.

---

## 🧠 Step 3: Interactive Demo Flow

### Scene 1: Welcome & Health Panel

- **Action**: Direct the examiner's attention to the sidebar under **🛡️ Service Health**.
- **Explanation**: _"I.N.A.Y.A.T. connects to three distinct AI cloud systems. The health monitor sidebar automatically probes Gemini, Mem0, and Neo4j at startup and reconnects dynamically if they go offline. All services are currently green and fully operational."_

### Scene 2: Memory Creation & Personalization

- **Action**: Enter your name in the sidebar profile (e.g. `Rahul`).
- **Action**: Type in chat: `"I am a machine learning student. I love NLP and knowledge graphs."`
- **Explanation**: _"When I type this, the system processes my profile and uses the Mem0 SDK to record these personal facts. This memory is stored persistently in the cloud."_

### Scene 3: Session Persistence (The Restart Test)

- **Action**: Close the browser tab or hit refresh on the browser.
- **Explanation**: _"In standard chatbots, a browser reload wipes the context. But notice that I.N.A.Y.A.T. preserves my profile name in the URL query parameters (`?user=Rahul`)."_
- **Action**: Type in chat: `"What do you know about me?"`
- **Response**: The agent will retrieve the memories from Mem0 and output: _"You are a machine learning student who loves NLP and knowledge graphs."_
- **Explanation**: _"Even after a session reset, the agent retains persistent, cross-session user awareness."_

### Scene 4: Hybrid Knowledge Graph RAG

- **Action**: Ask a question based on your PDF documents. (If using the auto-generated dummy: `"What does I.N.A.Y.A.T. stand for?"` or `"What circuit breaker does it use?"`).
- **Response**: The agent answers utilizing document chunks retrieved from the Neo4j Property Graph Store.
- **Explanation**: _"Instead of traditional simple vector search, the agent uses LlamaIndex's PropertyGraphIndex to query entity-relationship paths directly from Neo4j. This creates a hybrid search that is far more accurate and less prone to hallucination."_

### Scene 5: Graceful Failure & Self-Healing (The Circuit Breaker)

- **Action**: Check the box **🔥 Force Fail Mem0** in the sidebar.
- **Action**: Point out that the Service Health panel now shows `🔴 Forced Fail` for Mem0.
- **Action**: Type in chat: `"Who am I?"` or `"Hello!"`
- **Response**: The agent will still answer you perfectly (without personalization) rather than throwing a python stack trace and crashing the site.
- **Explanation**: _"Our custom CircuitBreaker class detected the failure. Instead of throwing an unhandled stack trace and crashing, the agent degrades gracefully, bypassing Mem0 and continuing to run on pure Gemini and Neo4j RAG. If I uncheck the box, the circuit breaker resets and memory functionality is restored."_

### Scene 6: Neo4j Visual Proof

- **Action**: Open your Neo4j AuraDB Console (`console.neo4j.io`) in a new tab.
- **Action**: Run the Cypher query: `MATCH (n) RETURN n LIMIT 30;`
- **Explanation**: _"Here is the raw visual proof of the Knowledge Graph index constructed from our documents. Every entity and relationship extracted from the text is stored as a node and link inside Neo4j."_
