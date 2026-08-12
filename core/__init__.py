"""I.N.A.Y.A.T. core package.

Submodules (strict SRP boundaries):
    settings        – Type-safe environment configuration
    identity        – User id parsing and sanitization
    observability   – Request correlation and span logging
    schemas         – Shared Pydantic contracts (QueryInput, QueryResult)
    conversation    – Short-term in-memory chat buffer
    compat          – Backwards-compatible query/build_index exports (§0.3)
    ingest          – Document upload persistence and index lifecycle
    agent           – RAG query and answer generation
    llm_setup       – Gemini LLM and embedding initialisation
    memory          – Mem0 cloud long-term memory
    graph_store     – Neo4j driver, Cypher, visualization payloads
    resilience      – Retry, circuit breaker, safe_execute
    logging_config  – Structured file + console logging
    health          – Service health monitor
    startup         – Boot orchestration
"""
