# -*- coding: utf-8 -*-
"""I.N.A.Y.A.T. — Main Streamlit Application.

Intelligent Neural Architecture for Yielding Agentic Thinking.
An AI agent that remembers, reads your documents, and shows its knowledge graph.

Launch:
    streamlit run app.py
"""

import time
import logging
import streamlit as st
from typing import Dict, List

# ── Bootstrap (must happen before any other core import) ──────────────
from core.startup import run_startup

_ok, _health, _warnings = run_startup()
logger = logging.getLogger("inayat")

# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="I.N.A.Y.A.T. — Agentic RAG",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global ─────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.main { background: #0a0a0f; }

/* ── Header ─────────────────────────────────── */
.hero-title {
    background: linear-gradient(135deg, #a78bfa 0%, #818cf8 40%, #6366f1 70%, #4f46e5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.6rem; font-weight: 800;
    letter-spacing: -0.03em;
    margin-bottom: 0;
}
.hero-sub {
    color: #71717a; font-size: 0.95rem; margin-top: 0.25rem;
}

/* ── Sidebar ────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f18 0%, #0a0a12 100%);
    border-right: 1px solid #1e1e2e;
}
.sidebar-brand {
    background: linear-gradient(135deg, #a78bfa, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.6rem; font-weight: 800;
    letter-spacing: -0.02em;
}

/* ── Status badges ──────────────────────────── */
.status-card {
    padding: 0.6rem 0.85rem;
    border-radius: 10px;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
    font-weight: 500;
    background: rgba(24, 24, 32, 0.7);
    border: 1px solid rgba(63, 63, 80, 0.4);
    backdrop-filter: blur(8px);
    display: flex; align-items: center; gap: 0.5rem;
}

/* ── Chat messages ──────────────────────────── */
.msg-user {
    background: linear-gradient(135deg, #1e1b4b 0%, #1a1740 100%);
    border: 1px solid #312e81;
    border-radius: 16px 16px 4px 16px;
    padding: 1rem 1.2rem; margin: 0.5rem 0;
    color: #e4e4e7;
    animation: fadeUp 0.25s ease-out;
}
.msg-assistant {
    background: linear-gradient(135deg, #18181b 0%, #1c1c24 100%);
    border: 1px solid #27272a;
    border-radius: 16px 16px 16px 4px;
    padding: 1rem 1.2rem; margin: 0.5rem 0;
    color: #d4d4d8;
    animation: fadeUp 0.25s ease-out;
}
.msg-role {
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em;
    font-weight: 700; margin-bottom: 0.35rem;
    color: #a78bfa;
}
.msg-role-ai { color: #34d399; }

/* ── Memory pills ───────────────────────────── */
.mem-pill {
    display: inline-block;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 100px;
    padding: 0.25rem 0.75rem;
    font-size: 0.78rem;
    color: #a5b4fc;
    margin: 0.2rem 0.2rem;
}

/* ── Animation ──────────────────────────────── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Thinking spinner ───────────────────────── */
.thinking {
    color: #818cf8; font-style: italic;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50%      { opacity: 1; }
}

/* ── File Uploader Styling ───────────────────── */
[data-testid="stFileUploader"] {
    background: rgba(24, 24, 32, 0.4) !important;
    border: 1px dashed rgba(167, 139, 250, 0.3) !important;
    border-radius: 12px !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploader"] button {
    background: linear-gradient(135deg, #a78bfa, #6366f1) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.4rem 1rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stFileUploader"] button:hover {
    box-shadow: 0 0 15px rgba(167, 139, 250, 0.5) !important;
    transform: translateY(-1px) !important;
}

/* ── Text Input Styling ─────────────────────── */
div[data-baseweb="input"] {
    background: rgba(15, 15, 24, 0.8) !important;
    border: 1px solid rgba(63, 63, 80, 0.5) !important;
    border-radius: 8px !important;
    color: #e4e4e7 !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
div[data-baseweb="input"]:focus-within {
    border-color: #818cf8 !important;
    box-shadow: 0 0 10px rgba(129, 140, 248, 0.35) !important;
}

/* ── Button Styling ─────────────────────────── */
button[kind="secondary"] {
    background: rgba(24, 24, 32, 0.7) !important;
    border: 1px solid rgba(63, 63, 80, 0.6) !important;
    border-radius: 8px !important;
    color: #e4e4e7 !important;
    transition: all 0.25s ease !important;
}
button[kind="secondary"]:hover {
    border-color: #a78bfa !important;
    color: #a78bfa !important;
    box-shadow: 0 0 10px rgba(167, 139, 250, 0.25) !important;
}

/* ── Checkbox Styling ───────────────────────── */
span[data-baseweb="checkbox"] > div {
    border-color: rgba(167, 139, 250, 0.5) !important;
}
[data-testid="stCheckbox"] label {
    color: #a1a1aa !important;
    font-size: 0.9rem !important;
}
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────

def _init_state() -> None:
    """Initialise all session state keys once."""
    # Pre-populate user_id from query params if available
    default_user = st.query_params.get("user", "")
    defaults = {
        "messages": [],
        "user_id": default_user,
        "health": _health,
        "startup_warnings": _warnings,
        "startup_ok": _ok,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_state()


# ── Cached service helpers ────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def _fetch_memories(user_id: str) -> List[str]:
    """Retrieve user memories, cached for 30 s to avoid hammering Mem0."""
    from core.memory import get_memories
    return get_memories(user_id)


@st.cache_resource(show_spinner=False)
def _get_health_monitor():
    """Singleton health monitor."""
    from core.health import HealthMonitor
    return HealthMonitor()


# ── Sidebar ───────────────────────────────────────────────────────────

def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("<div class='sidebar-brand'>I.N.A.Y.A.T.</div>", unsafe_allow_html=True)
        st.caption("Intelligent Neural Architecture for Yielding Agentic Thinking")
        st.markdown("---")

        # User profile
        st.markdown("##### 👤 User Profile")
        name = st.text_input(
            "Your name",
            value=st.session_state.user_id,
            placeholder="e.g. Moham",
            label_visibility="collapsed",
        )
        if name != st.session_state.user_id:
            st.session_state.user_id = name
            st.query_params["user"] = name
            st.rerun()

        st.markdown("---")

        # Document Ingestion
        st.markdown("##### 📂 Ingest Documents")
        uploaded_files = st.file_uploader(
            "Upload PDFs or TXT files",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded_files:
            import os
            os.makedirs("data/documents", exist_ok=True)
            new_file_saved = False
            for f in uploaded_files:
                fpath = os.path.join("data/documents", f.name)
                if not os.path.exists(fpath):
                    with open(fpath, "wb") as out_f:
                        out_f.write(f.getbuffer())
                    new_file_saved = True
                    st.success(f"Saved {f.name}")
            
            if new_file_saved:
                with st.spinner("Indexing new files..."):
                    from core.agent import build_index
                    build_index()
                    st.success("Graph Index updated!")
                    st.rerun()

        st.markdown("---")

        # Health panel
        st.markdown("##### 🛡️ Service Health")
        if st.button("🔄 Refresh", use_container_width=True):
            with st.spinner("Probing services…"):
                monitor = _get_health_monitor()
                st.session_state.health = monitor.run_all()

        h = st.session_state.health
        
        # Override health display if forced failures are active
        import core.memory as mem
        import core.graph_store as gs
        
        is_mem_forced = getattr(mem._cb, "forced_open", False)
        is_graph_forced = getattr(gs._cb, "forced_open", False)

        for svc, label in [("gemini", "Gemini LLM"), ("mem0", "Mem0 Memory"), ("neo4j", "Neo4j Graph")]:
            status = h.get(svc, "⚪ Unknown")
            if svc == "mem0" and is_mem_forced:
                status = "🔴 Forced Fail"
            elif svc == "neo4j" and is_graph_forced:
                status = "🔴 Forced Fail"
            st.markdown(f"<div class='status-card'>{status}&ensp;{label}</div>", unsafe_allow_html=True)

        # Startup warnings
        for w in st.session_state.startup_warnings:
            st.warning(w, icon="⚠️")

        # Resilience Testing Panel
        st.markdown("---")
        st.markdown("##### 🧪 Resilience Testing")
        
        fail_mem0 = st.checkbox("🔥 Force Fail Mem0", value=is_mem_forced)
        if fail_mem0 != is_mem_forced:
            mem._cb.forced_open = fail_mem0
            st.rerun()
            
        fail_neo4j = st.checkbox("🔥 Force Fail Neo4j", value=is_graph_forced)
        if fail_neo4j != is_graph_forced:
            gs._cb.forced_open = fail_neo4j
            st.rerun()
            
        if fail_mem0 or fail_neo4j:
            st.warning("Circuit breaker(s) forced OPEN. Systems running in degraded mode.")

        st.markdown("---")

        # Actions
        st.markdown("##### ⚙️ Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑 Clear Memory", use_container_width=True):
                if st.session_state.user_id:
                    from core.memory import clear_memories
                    if clear_memories(st.session_state.user_id):
                        st.success("Memories cleared.")
                        _fetch_memories.clear()
                    else:
                        st.error("Failed to clear.")
        with col2:
            if st.button("🧹 New Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

        st.markdown("---")
        with st.expander("📜 Demo Script Guide"):
            st.markdown("""
**1. Welcome & Warmup**
- Point out Service Health: all services `🟢 Connected`.

**2. Memory Injection**
- Enter name: e.g. **Rahul**
- Say: `I am a machine learning student. I love NLP.`
- Facts are stored in Mem0 cloud.

**3. Persistence Test**
- Hard-refresh the page (simulated browser restart).
- The URL preserves `?user=Rahul`.
- Ask: `What do you know about me?`
- Agent recalls your facts from Mem0.

**4. Knowledge Graph RAG**
- Ask: `What does I.N.A.Y.A.T. use for embedding?`
- Answer is retrieved from Neo4j AuraDB graph.

**5. Graceful Failure**
- Check `Force Fail Mem0` or `Force Fail Neo4j`.
- Notice the service health updates.
- Ask again: the app handles it gracefully and doesn't crash!
            """)


# ── Chat renderer ─────────────────────────────────────────────────────

def _render_message(role: str, content: str) -> None:
    """Display a single chat bubble."""
    if role == "user":
        st.markdown(
            f"<div class='msg-user'><div class='msg-role'>You</div>{content}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='msg-assistant'><div class='msg-role msg-role-ai'>I.N.A.Y.A.T.</div>{content}</div>",
            unsafe_allow_html=True,
        )


# ── Main page ─────────────────────────────────────────────────────────

def main() -> None:
    """Run the main Streamlit UI loop."""

    _render_sidebar()

    # ── Startup gate ──────────────────────────────────────────────────
    if not st.session_state.startup_ok:
        st.error("### ⚠️ Critical Configuration Missing")
        st.markdown(
            "Duplicate **`.env.example`** → **`.env`** and add your API keys, "
            "then restart the app."
        )
        st.stop()

    # ── Pre-warm Knowledge Graph Index ────────────────────────────────
    if "index_warmed" not in st.session_state:
        with st.spinner("🧠 Bootstrapping PropertyGraphIndex (Neo4j)..."):
            try:
                from core.agent import get_index
                get_index()
                st.session_state.index_warmed = True
                st.session_state.startup_warning_details = None
            except Exception as e:
                st.session_state.startup_warning_details = str(e)
                st.session_state.index_warmed = False

    # ── Sandbox warning indicator ──
    if getattr(st.session_state, "startup_warning_details", None):
        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.25); 
                    padding: 0.85rem 1.2rem; border-radius: 12px; margin-bottom: 1.5rem; 
                    display: flex; align-items: center; gap: 0.75rem; color: #fcd34d; font-size: 0.88rem;">
            <span>⚠️</span>
            <div>
                <strong>Sandbox Mode Active:</strong> External API credentials missing or invalid. Agent queries will fall back to direct LLM fallback and mock data structures.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────
    st.markdown("<div class='hero-title'>I.N.A.Y.A.T.</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-sub'>"
        "An agentic RAG system that remembers you, reads your documents, "
        "and visualises its knowledge graph."
        "</div>",
        unsafe_allow_html=True,
    )

    if not st.session_state.user_id:
        # Render a gorgeous 2026-style MCA Final Project landing page!
        st.markdown("""
        <div style="padding: 1rem 0; margin-top: 0.5rem; animation: fadeUp 0.4s ease-out; text-align: center;">
            <div style="background: linear-gradient(135deg, rgba(167, 139, 250, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%); 
                        border: 1px solid rgba(167, 139, 250, 0.18); 
                        padding: 3.5rem 2rem; border-radius: 24px; max-width: 850px; margin: 0 auto;
                        box-shadow: 0 20px 40px rgba(0,0,0,0.5); backdrop-filter: blur(16px);">
        """, unsafe_allow_html=True)

        col_img1, col_img2, col_img3 = st.columns([1, 1, 1])
        with col_img2:
            st.image("assets/logo.png", use_container_width=True)

        st.markdown("""
                <h2 style="background: linear-gradient(135deg, #a78bfa 0%, #818cf8 50%, #6366f1 100%);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                           font-size: 2.8rem; font-weight: 800; margin-top: 1rem; margin-bottom: 0.75rem; letter-spacing: -0.03em;">
                    I.N.A.Y.A.T.
                </h2>
                <p style="color: #a1a1aa; font-size: 1.1rem; max-width: 650px; margin: 0 auto 2.5rem auto; line-height: 1.6; font-weight: 300;">
                    Intelligent Neural Architecture for Yielding Agentic Thinking.<br/>
                    A state-of-the-art agentic RAG solution utilizing <b>LlamaIndex Property Graphs</b>, <b>Neo4j AuraDB</b>, and <b>Mem0</b> persistent context.
                </p>
                <div style="background: rgba(15, 15, 24, 0.5); border: 1px solid rgba(63, 63, 80, 0.4); 
                            border-radius: 16px; padding: 1.8rem; max-width: 480px; margin: 0 auto 1.5rem auto; box-shadow: inset 0 2px 4px rgba(0,0,0,0.4); text-align: center;">
                    <div style="color: #e4e4e7; font-weight: 600; margin-bottom: 1rem; font-size: 0.95rem;">
                        👤 Initialize Demo Profile Workspace
                    </div>
        """, unsafe_allow_html=True)

        col_space1, col_input, col_space2 = st.columns([1, 3, 1])
        with col_input:
            name_input = st.text_input(
                "Profile Name",
                placeholder="e.g. Moham",
                key="landing_name_input",
                label_visibility="collapsed"
            )
            if st.button("🚀 Enter Agentic Workspace", use_container_width=True):
                if name_input.strip():
                    st.session_state.user_id = name_input.strip()
                    st.query_params["user"] = name_input.strip()
                    st.rerun()
                else:
                    st.warning("Please enter a name to proceed.")

        st.markdown("""
                </div>
            </div>
        </div>
        
        <div style="margin-top: 3.5rem;">
            <h3 style="text-align: center; color: #f4f4f5; font-size: 1.5rem; font-weight: 700; margin-bottom: 2rem; letter-spacing: -0.02em;">
                🛡️ Core Architectural Pillars
            </h3>
            <div style="display: flex; gap: 1.5rem; justify-content: center; flex-wrap: wrap; max-width: 1000px; margin: 0 auto; text-align: left;">
                <div style="flex: 1; min-width: 280px; background: rgba(15, 15, 24, 0.4); border: 1px solid rgba(167, 139, 250, 0.15); 
                            padding: 1.8rem; border-radius: 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.25);">
                    <div style="font-size: 2rem; margin-bottom: 0.75rem;">🧠</div>
                    <h4 style="color: #a78bfa; font-size: 1.15rem; font-weight: 600; margin-bottom: 0.5rem; margin-top: 0;">Persistent Memory</h4>
                    <p style="color: #a1a1aa; font-size: 0.88rem; line-height: 1.5; margin: 0; font-weight: 300;">
                        Integrates Mem0 cloud infrastructure to extract, store, and recall personal facts and user preferences dynamically across application sessions.
                    </p>
                </div>
                <div style="flex: 1; min-width: 280px; background: rgba(15, 15, 24, 0.4); border: 1px solid rgba(99, 102, 241, 0.15); 
                            padding: 1.8rem; border-radius: 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.25);">
                    <div style="font-size: 2rem; margin-bottom: 0.75rem;">🕸️</div>
                    <h4 style="color: #818cf8; font-size: 1.15rem; font-weight: 600; margin-bottom: 0.5rem; margin-top: 0;">Knowledge Graph RAG</h4>
                    <p style="color: #a1a1aa; font-size: 0.88rem; line-height: 1.5; margin: 0; font-weight: 300;">
                        Combines LlamaIndex with Neo4j AuraDB graph databases to traverse entity-relation nodes, delivering high-precision contextual search results.
                    </p>
                </div>
                <div style="flex: 1; min-width: 280px; background: rgba(15, 15, 24, 0.4); border: 1px solid rgba(52, 211, 153, 0.15); 
                            padding: 1.8rem; border-radius: 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.25);">
                    <div style="font-size: 2rem; margin-bottom: 0.75rem;">🛡️</div>
                    <h4 style="color: #34d399; font-size: 1.15rem; font-weight: 600; margin-bottom: 0.5rem; margin-top: 0;">Self-Healing Resilience</h4>
                    <p style="color: #a1a1aa; font-size: 0.88rem; line-height: 1.5; margin: 0; font-weight: 300;">
                        Implemented with custom active circuit breakers that isolate connection faults and downgrade gracefully, maintaining uptime at all times.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Create Tabs
    tab1, tab2 = st.tabs(["💬 Agent Chat", "🕸️ Knowledge Graph Visualizer"])

    with tab1:
        # ── Memory display ────────────────────────────────────────────────
        memories = _fetch_memories(st.session_state.user_id)
        if memories:
            with st.expander(f"🧠 Long-Term Memory  ({len(memories)} facts)", expanded=False):
                pills = "".join(f"<span class='mem-pill'>{m}</span>" for m in memories)
                st.markdown(pills, unsafe_allow_html=True)

        st.markdown("---")

        # ── Chat history ──────────────────────────────────────────────────
        for msg in st.session_state.messages:
            _render_message(msg["role"], msg["content"])

    with tab2:
        st.markdown("### 🕸️ Knowledge Graph Visualizer")
        st.markdown(
            "This interactive canvas displays the entity-relationship paths extracted from your documents "
            "and stored in Neo4j. If Neo4j is offline or empty, a mock graph of the I.N.A.Y.A.T. system architecture is shown."
        )
        
        from core.graph_store import get_visualization_data
        graph_data = get_visualization_data()
        
        nodes_js = "[" + ",".join([
            f"{{id: {n['id']}, label: '{n['label']}', group: '{n['group']}'}}"
            for n in graph_data["nodes"]
        ]) + "]"
        
        edges_js = "[" + ",".join([
            f"{{from: {e['from']}, to: {e['to']}, label: '{e['label']}'}}"
            for e in graph_data["edges"]
        ]) + "]"
        
        is_mock_banner = "⚠️ **Showing System Architecture Graph** (Neo4j is empty or offline)" if graph_data["is_mock"] else "🟢 **Connected to Neo4j AuraDB** (Live Knowledge Graph)"
        st.info(is_mock_banner)
        
        # Generate Vis.js Network HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style type="text/css">
                #mynetwork {{
                    width: 100%;
                    height: 500px;
                    border: 1px solid #27272a;
                    background-color: #0c0c14;
                    border-radius: 12px;
                }}
            </style>
        </head>
        <body>
        <div id="mynetwork"></div>
        <script type="text/javascript">
            var nodes = new vis.DataSet({nodes_js});
            var edges = new vis.DataSet({edges_js});
            var container = document.getElementById('mynetwork');
            var data = {{
                nodes: nodes,
                edges: edges
            }};
            var options = {{
                nodes: {{
                    shape: 'dot',
                    size: 24,
                    font: {{
                        color: '#ffffff',
                        size: 14,
                        face: 'Inter, sans-serif'
                    }},
                    borderWidth: 2,
                    shadow: true
                }},
                edges: {{
                    width: 2,
                    color: {{ color: '#818cf8', highlight: '#a78bfa' }},
                    font: {{
                        color: '#a5b4fc',
                        size: 11,
                        align: 'horizontal',
                        background: '#0c0c14'
                    }},
                    arrows: {{
                        to: {{ enabled: true, scaleFactor: 0.8 }}
                    }},
                    smooth: {{
                        type: 'cubicBezier',
                        forceDirection: 'none',
                        roundness: 0.5
                    }}
                }},
                groups: {{
                    Agent: {{ color: {{ background: '#a78bfa', border: '#818cf8' }} }},
                    LLM: {{ color: {{ background: '#34d399', border: '#059669' }} }},
                    Memory: {{ color: {{ background: '#60a5fa', border: '#2563eb' }} }},
                    GraphStore: {{ color: {{ background: '#fb7185', border: '#e11d48' }} }},
                    Resilience: {{ color: {{ background: '#fbbf24', border: '#d97706' }} }},
                    User: {{ color: {{ background: '#f472b6', border: '#db2777' }} }},
                    Entity: {{ color: {{ background: '#94a3b8', border: '#475569' }} }},
                    Chunk: {{ color: {{ background: '#475569', border: '#334155' }} }}
                }},
                physics: {{
                    stabilization: true,
                    barnesHut: {{
                        gravitationalConstant: -2000,
                        springConstant: 0.04,
                        springLength: 95
                    }}
                }}
            }};
            var network = new vis.Network(container, data, options);
        </script>
        </body>
        </html>
        """
        st.components.v1.html(html_content, height=520)

    st.markdown("---")

    # ── User input ────────────────────────────────────────────────────
    if prompt := st.chat_input("Ask about your documents, or tell me about yourself…"):
        # Display user bubble immediately
        st.session_state.messages.append({"role": "user", "content": prompt})
        _render_message("user", prompt)

        # Save to Mem0 (fire-and-forget, non-blocking)
        from core.memory import add_memory
        add_memory(st.session_state.user_id, prompt)

        # Build memory context for the agent
        mem_lines = _fetch_memories(st.session_state.user_id)
        memory_ctx = "\n".join(f"• {m}" for m in mem_lines) if mem_lines else ""

        # Query the agent
        st.markdown("<div class='thinking'>Thinking…</div>", unsafe_allow_html=True)
        from core.agent import query as agent_query
        answer = agent_query(prompt, memory_context=memory_ctx)

        # Display assistant bubble
        st.session_state.messages.append({"role": "assistant", "content": answer})

        # Context window safety: keep last 10 turns only
        if len(st.session_state.messages) > 20:
            st.session_state.messages = st.session_state.messages[-20:]

        st.rerun()


if __name__ == "__main__":
    main()
