# I.N.A.Y.A.T. — RGPV Project Report (Ready Draft)

## Page 1: Cover Page

**Project Title:**  
**I.N.A.Y.A.T. — Intelligent Neural Architecture for Yielding Agentic Thinking**  
*An agentic RAG system that remembers users, reads documents, and visualizes knowledge graphs.*

**Submitted By:** ____________________  
**Enrollment No.:** ____________________  
**Branch:** MCA  
**Semester:** 4th Semester  
**Session:** 2025–26  
**College:** ____________________  
**University:** Rajiv Gandhi Proudyogiki Vishwavidyalaya (RGPV), Bhopal  
**Guide Name:** ____________________

---

## Page 2: Index / Table of Contents

1. Abstract  
2. Introduction  
3. Problem Statement  
4. Objectives  
5. Existing vs Proposed System  
6. System Architecture  
7. Technology Stack  
8. Module Description  
9. Actual Working (Execution Flow)  
10. Testing and Results  
11. Conclusion and Future Scope  
12. References

---

## Page 2 (continued): Abstract and Keywords

### Abstract
I.N.A.Y.A.T. is an agentic Retrieval-Augmented Generation (RAG) system developed to solve practical limitations of normal chatbots. Traditional systems are mostly stateless and forget user context after session reset. This project introduces persistent memory, isolated user workspaces, graph-based document retrieval, and resilience mechanisms for production-style reliability.

The system uses Google Gemini for response generation, Mem0 for long-term user memory, Neo4j AuraDB for graph storage, and LlamaIndex PropertyGraphIndex for hybrid retrieval from uploaded documents. It supports user-specific document ingestion, memory-aware responses, and visual graph interaction through a Streamlit interface. If external services fail, circuit breaker and safe execution layers prevent crashes and provide graceful fallback responses.

This project demonstrates how modern agentic AI can be made personalized, explainable, and robust for real-world educational and enterprise scenarios.

### Keywords
Agentic AI, RAG, LlamaIndex, Neo4j, Mem0, Gemini, Streamlit, Knowledge Graph, Circuit Breaker, Resilience

---

## Page 3: Introduction and Problem Statement

### 1. Introduction
I.N.A.Y.A.T. stands for **Intelligent Neural Architecture for Yielding Agentic Thinking**. It is designed as a next-generation AI assistant that combines conversational intelligence, long-term memory, and graph-structured retrieval from documents. The main purpose is to provide more meaningful and context-aware responses than generic chatbots.

In this system, users can upload PDF/TXT documents, ask questions, and receive responses grounded in retrieved graph context. The assistant can also remember user-specific facts and preferences over time, making interactions personalized and continuous.

### 2. Problem Statement
Most chatbot systems face the following issues:
- They do not remember user-specific context across sessions.
- They use only flat retrieval and often miss semantic relationships in documents.
- They can crash or become unusable when external APIs are unavailable.
- They are weak in multi-user isolation where each user needs separate context.

I.N.A.Y.A.T. addresses these gaps using memory isolation, graph RAG, and resilient architecture.

---

## Page 4: Objectives and Existing vs Proposed System

### 3. Objectives
1. Implement persistent long-term memory for each user profile.
2. Support ingestion and indexing of PDF/TXT documents.
3. Enable graph-based retrieval with entity-relation context.
4. Provide clear visual understanding of knowledge graph structure.
5. Ensure fault tolerance using retries, circuit breakers, and fallback logic.
6. Integrate testing and CI checks for production-like quality assurance.

### 4. Existing vs Proposed System

| Parameter | Existing Chatbot Systems | Proposed I.N.A.Y.A.T. System |
|---|---|---|
| User Memory | Temporary / session-only | Persistent with Mem0 |
| Retrieval | Mostly vector-only or keyword-only | Hybrid graph RAG with LlamaIndex + Neo4j |
| Multi-user Isolation | Weak or manual | Isolated profile context and docs |
| Failure Handling | Often crashes or hard errors | Graceful degradation with resilience wrappers |
| Explainability | Limited | Graph visualization with node/edge context |

---

## Page 5: System Architecture

### 5. Architecture Overview
The architecture follows a coordinated agentic pipeline:

1. User interacts with Streamlit UI.
2. Startup and health modules validate environment and service states.
3. Memory service fetches user history.
4. Graph retrieval service fetches user-filtered document context.
5. Gemini generates response from augmented prompt.
6. Updated facts are saved back to memory.
7. Graph panel visualizes associated entities and chunks.

### 5.1 Core Components
- **UI Layer:** `app.py` (Streamlit workspace)
- **Agent Layer:** `core/agent.py` (RAG + fallback)
- **Memory Layer:** `core/memory.py` (Mem0 operations)
- **Graph Layer:** `core/graph_store.py` (Neo4j + visualization)
- **Resilience Layer:** `core/resilience.py` (safe execution and circuit breaker)
- **Health Layer:** `core/health.py` (service monitoring)

### 5.2 Suggested Diagram for Report
Use the architecture flow from README (user input → health checks → memory/graph retrieval → LLM response → memory/graph update).

---

## Page 6: Technology Stack and Project Structure

### 6. Technology Stack

| Layer | Technology | Role |
|---|---|---|
| Frontend/UI | Streamlit | Chat workspace, upload, health, graph view |
| LLM | Google Gemini Flash | Response generation |
| Memory | Mem0 | Persistent user facts |
| Graph DB | Neo4j AuraDB | Knowledge graph storage |
| RAG Framework | LlamaIndex PropertyGraphIndex | Document indexing + retrieval |
| Backend Utilities | Python, Tenacity | Resilience and retry |
| Validation | unittest, flake8, black, GitHub Actions | Quality and CI checks |

### 6.1 Project Structure (Important Files)
- `app.py`: Main user interface and orchestration
- `core/agent.py`: Query execution, graph RAG, LLM fallback
- `core/memory.py`: Memory add/get/search/clear
- `core/graph_store.py`: Neo4j connection, cypher execution, graph data
- `core/health.py`: Service-level health checks
- `core/resilience.py`: retry/circuit-breaker/safe_execute
- `tests/smoke_test.py`: baseline functional checks
- `tests/backend_feature_test.py`: deeper backend integration checks
- `.github/workflows/ci.yml`: lint, secret scan, smoke test pipeline

---

## Page 7: Module Description

### 7.1 `app.py` (Streamlit Orchestrator)
- Manages user session and profile isolation.
- Handles file upload and triggers indexing.
- Displays service health and resilience toggles.
- Renders chat messages and graph panel.

### 7.2 `core/agent.py` (RAG Agent)
- Builds/loads `PropertyGraphIndex` from user documents.
- Executes user-filtered graph query engine.
- Detects weak/no-context RAG outputs.
- Falls back to direct Gemini response when needed.

### 7.3 `core/memory.py` (Mem0 Integration)
- Adds and retrieves user memories.
- Supports memory search and clear operations.
- Uses circuit breaker protection around memory calls.

### 7.4 `core/graph_store.py` (Neo4j Layer)
- Creates and caches Neo4j driver.
- Runs read/write Cypher safely.
- Exposes visualization data for UI graph rendering.

### 7.5 `core/health.py` + `core/resilience.py`
- Health monitor tracks Gemini, Mem0, Neo4j status.
- Resilience utilities provide retry and graceful failure behavior.

---

## Page 8: Actual Working (Execution Flow)

### 8. Step-by-Step Working
1. Application starts and loads environment configuration.
2. Startup validator checks critical and recommended variables.
3. Health monitor probes Gemini, Mem0, and Neo4j.
4. User enters profile name (example: Rahul).
5. User uploads PDF/TXT files in profile-specific folder.
6. System builds graph index with `user_id` metadata tagging.
7. User asks a question in chat.
8. Agent fetches profile memories from Mem0.
9. Agent queries graph RAG engine with user filters.
10. If graph retrieval is insufficient or unavailable, fallback to Gemini direct completion.
11. Response is shown to user, and memory is updated for future sessions.
12. Graph panel shows related nodes and relationships for visual verification.

### 8.1 Example Query Flow
- User says: “I am interested in NLP and knowledge graphs.”
- Memory stores this preference in Mem0.
- User later asks: “What do you know about me?”
- Agent recalls facts and responds with personalized context.
- If graph services are down, assistant still answers in degraded mode.

---

## Page 9: Testing and Results

### 9.1 Testing Strategy
- **Smoke tests (`tests/smoke_test.py`)**
  - Module import checks
  - Environment validation checks
  - Health monitor and resilience utility checks
- **Backend feature tests (`tests/backend_feature_test.py`)**
  - Startup and env checks
  - LLM and embedding checks
  - Memory CRUD flow
  - Neo4j graph operations
  - RAG query behavior
- **CI Workflow (`.github/workflows/ci.yml`)**
  - flake8 critical lint check
  - black formatting check
  - gitleaks secret scanning
  - smoke test execution

### 9.2 Result Summary Table

| Test Area | Outcome |
|---|---|
| Smoke Test Suite | Passes locally (service-dependent tests skipped without keys) |
| Backend Feature Suite | Requires live API credentials; fails in no-key sandbox |
| Lint (flake8 critical) | Pass |
| Format Check (black) | Existing repo has unrelated formatting differences |
| Resilience Behavior | Graceful fallback observed for service outages |

### 9.3 Observed Working Result
System functions as a robust personalized RAG assistant with memory, graph retrieval, and visual evidence of knowledge structure.

---

## Page 10: Conclusion, Future Scope, References

### 10. Conclusion
I.N.A.Y.A.T. successfully demonstrates an agentic AI architecture that is user-aware, document-grounded, and resilient. The combination of Mem0 memory, Neo4j graph retrieval, LlamaIndex indexing, and Gemini generation creates a practical and exam-ready system beyond basic chatbot behavior. The project is modular, testable, and presentation-friendly for academic evaluation.

### 11. Future Scope
1. Role-based access and authentication for enterprise multi-user deployments.
2. Expanded document support (DOCX, PPTX, scanned OCR pipelines).
3. Better source citation UI with confidence scoring.
4. Scheduled graph maintenance and summarization jobs.
5. Containerized cloud deployment with monitoring dashboard.

### 12. References
1. LlamaIndex Documentation — https://docs.llamaindex.ai/  
2. Neo4j Documentation — https://neo4j.com/docs/  
3. Streamlit Documentation — https://docs.streamlit.io/  
4. Google Gemini API Docs — https://ai.google.dev/  
5. Mem0 Documentation — https://docs.mem0.ai/  
6. Project Repository Files: `README.md`, `CONTEXT.md`, `core/*`, `tests/*`, `.github/workflows/ci.yml`

---

## Appendix (Optional for submission if extra page allowed)
- Screenshots:
  - Health panel showing connected services
  - Chat showing personalized memory retrieval
  - Graph visualization panel
  - CI checks in GitHub Actions
