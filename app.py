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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

/* ── Global ─────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}
.main {
    background: radial-gradient(circle at 50% 0%, #0c0b1c 0%, #040408 75%);
}

/* Custom scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #06060c;
}
::-webkit-scrollbar-thumb {
    background: rgba(167, 139, 250, 0.25);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(167, 139, 250, 0.5);
}

/* ── Header ─────────────────────────────────── */
.hero-title {
    background: linear-gradient(135deg, #c084fc 0%, #818cf8 35%, #6366f1 70%, #4f46e5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem; font-weight: 800;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: -0.04em;
    margin-bottom: 0;
    filter: drop-shadow(0 2px 8px rgba(129, 140, 248, 0.2));
}
.hero-sub {
    color: #a1a1aa; font-size: 0.95rem; margin-top: 0.25rem; font-weight: 300;
}

/* ── Sidebar ────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #07070d 0%, #030306 100%);
    border-right: 1px solid rgba(167, 139, 250, 0.15);
}
.sidebar-brand {
    background: linear-gradient(135deg, #c084fc, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.8rem; font-weight: 800;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: -0.03em;
}

/* ── Status badges ──────────────────────────── */
.status-card {
    padding: 0.7rem 0.95rem;
    border-radius: 12px;
    margin-bottom: 0.6rem;
    font-size: 0.85rem;
    font-weight: 500;
    background: rgba(15, 15, 25, 0.7);
    border: 1px solid rgba(167, 139, 250, 0.15);
    backdrop-filter: blur(12px);
    display: flex; align-items: center; gap: 0.6rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    transition: all 0.25s ease;
}
.status-card:hover {
    border-color: rgba(167, 139, 250, 0.35);
    box-shadow: 0 4px 20px rgba(167, 139, 250, 0.15);
    transform: translateY(-1px);
}

/* ── Chat messages ──────────────────────────── */
.msg-user {
    background: linear-gradient(135deg, rgba(30, 27, 75, 0.65) 0%, rgba(20, 18, 55, 0.75) 100%);
    border: 1px solid rgba(129, 140, 248, 0.25);
    border-radius: 18px 18px 4px 18px;
    padding: 1rem 1.25rem; margin: 0.65rem 0;
    color: #f4f4f5;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    backdrop-filter: blur(8px);
    animation: fadeUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.msg-assistant {
    background: linear-gradient(135deg, rgba(20, 20, 28, 0.7) 0%, rgba(15, 15, 22, 0.8) 100%);
    border: 1px solid rgba(167, 139, 250, 0.2);
    border-radius: 18px 18px 18px 4px;
    padding: 1rem 1.25rem; margin: 0.65rem 0;
    color: #e4e4e7;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    backdrop-filter: blur(8px);
    animation: fadeUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.msg-role {
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;
    font-weight: 700; margin-bottom: 0.4rem;
    color: #c084fc;
    font-family: 'Space Grotesk', sans-serif;
}
.msg-role-ai {
    color: #34d399;
    text-shadow: 0 0 8px rgba(52, 211, 153, 0.3);
}

/* ── Memory pills ───────────────────────────── */
.mem-pill {
    display: inline-block;
    background: rgba(167, 139, 250, 0.1);
    border: 1px solid rgba(167, 139, 250, 0.25);
    border-radius: 100px;
    padding: 0.3rem 0.85rem;
    font-size: 0.78rem;
    color: #c084fc;
    margin: 0.25rem 0.25rem;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    transition: all 0.2s ease;
}
.mem-pill:hover {
    border-color: rgba(167, 139, 250, 0.5);
    background: rgba(167, 139, 250, 0.15);
    transform: scale(1.02);
}

/* ── Animation ──────────────────────────────── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Thinking spinner ───────────────────────── */
.thinking {
    color: #c084fc; font-style: italic; font-size: 0.9rem;
    padding: 0.5rem 1rem;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 0.6; }
    50%      { opacity: 1; }
}

/* ── File Uploader Styling ───────────────────── */
[data-testid="stFileUploader"] {
    background: rgba(13, 13, 23, 0.5) !important;
    border: 1px dashed rgba(167, 139, 250, 0.25) !important;
    border-radius: 14px !important;
    padding: 0.6rem !important;
}
[data-testid="stFileUploader"] button {
    background: linear-gradient(135deg, #c084fc, #6366f1) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.45rem 1.1rem !important;
    font-weight: 600 !important;
    transition: all 0.25s ease !important;
}
[data-testid="stFileUploader"] button:hover {
    box-shadow: 0 0 15px rgba(167, 139, 250, 0.4) !important;
    transform: translateY(-1px) !important;
}

/* ── Text Input Styling ─────────────────────── */
div[data-baseweb="input"] {
    background: rgba(8, 8, 15, 0.9) !important;
    border: 1px solid rgba(167, 139, 250, 0.2) !important;
    border-radius: 10px !important;
    color: #f4f4f5 !important;
    transition: all 0.25s ease !important;
}
div[data-baseweb="input"]:focus-within {
    border-color: #818cf8 !important;
    box-shadow: 0 0 12px rgba(129, 140, 248, 0.3) !important;
}

/* ── Button Styling ─────────────────────────── */
button[kind="secondary"] {
    background: rgba(13, 13, 23, 0.8) !important;
    border: 1px solid rgba(167, 139, 250, 0.2) !important;
    border-radius: 10px !important;
    color: #e4e4e7 !important;
    transition: all 0.25s ease !important;
}
button[kind="secondary"]:hover {
    border-color: #c084fc !important;
    color: #c084fc !important;
    box-shadow: 0 0 12px rgba(167, 139, 250, 0.2) !important;
}

/* ── Checkbox Styling ───────────────────────── */
span[data-baseweb="checkbox"] > div {
    border-color: rgba(167, 139, 250, 0.5) !important;
}
[data-testid="stCheckbox"] label {
    color: #a1a1aa !important;
    font-size: 0.9rem !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────

def _init_state() -> None:
    """Initialise all session state keys once."""
    # Pre-populate user_id from query params if available
    default_user = st.query_params.get("user", "")
    if default_user and f"messages_{default_user}" not in st.session_state:
        st.session_state[f"messages_{default_user}"] = []
    defaults = {
        "messages": st.session_state.get(f"messages_{default_user}", []) if default_user else [],
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
            if st.session_state.user_id:
                st.session_state[f"messages_{st.session_state.user_id}"] = st.session_state.messages
            st.session_state.user_id = name
            st.query_params["user"] = name
            st.session_state.messages = st.session_state.get(f"messages_{name}", [])
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
            user_doc_dir = os.path.join("data", "documents", st.session_state.user_id)
            os.makedirs(user_doc_dir, exist_ok=True)
            new_file_saved = False
            for f in uploaded_files:
                fpath = os.path.join(user_doc_dir, f.name)
                if not os.path.exists(fpath):
                    with open(fpath, "wb") as out_f:
                        out_f.write(f.getbuffer())
                    new_file_saved = True
                    st.success(f"Saved {f.name}")
            
            if new_file_saved:
                with st.spinner("Indexing new files..."):
                    from core.agent import build_index
                    build_index(st.session_state.user_id)
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
        
        fail_mem0 = st.checkbox("🔥 Force Fail Mem0", value=is_mem_forced, key="resilience_fail_mem0")
        if fail_mem0 != is_mem_forced:
            mem._cb.forced_open = fail_mem0
            st.rerun()
            
        fail_neo4j = st.checkbox("🔥 Force Fail Neo4j", value=is_graph_forced, key="resilience_fail_neo4j")
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

    # ── Side-by-Side Unified Workspace ────────────────────────────────────
    col_left, col_right = st.columns([5, 7], gap="medium")

    with col_left:
        st.markdown("<h3 style='margin-top:0; color:#f4f4f5; font-size:1.4rem; font-weight:700;'>💬 Workspace Chat</h3>", unsafe_allow_html=True)
        
        # ── Memory display ────────────────────────────────────────────────
        memories = _fetch_memories(st.session_state.user_id)
        if memories:
            with st.expander(f"🧠 Long-Term Memory  ({len(memories)} facts)", expanded=False):
                pills = "".join(f"<span class='mem-pill'>{m}</span>" for m in memories)
                st.markdown(pills, unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # ── Chat history container ────────────────────────────────────────
        for msg in st.session_state.messages:
            _render_message(msg["role"], msg["content"])

        # ── User input ────────────────────────────────────────────────────
        if prompt := st.chat_input("Ask about your documents, or tell me about yourself…"):
            # Display user bubble immediately
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

    with col_right:
        st.markdown("<h3 style='margin-top:0; color:#f4f4f5; font-size:1.4rem; font-weight:700;'>🕸️ Neural Architecture Graph</h3>", unsafe_allow_html=True)
        
        from core.graph_store import get_visualization_data
        graph_data = get_visualization_data(st.session_state.user_id)
        
        import json
        nodes_js = json.dumps(graph_data["nodes"])
        edges_js = json.dumps(graph_data["edges"])
        
        is_mock_banner = "⚠️ **Showing System Architecture Graph** (Neo4j is empty or offline)" if graph_data["is_mock"] else "🟢 **Connected to Neo4j AuraDB** (Live Knowledge Graph)"
        st.info(is_mock_banner)
        
        # Generate Vis.js Network HTML with detailed interactive panel
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style type="text/css">
                @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: #040408;
                    font-family: 'Outfit', sans-serif;
                    overflow: hidden;
                }}
                #container-split {{
                    display: flex;
                    flex-direction: row;
                    width: 100%;
                    height: 520px;
                    background: #080810;
                    border: 1px solid rgba(167, 139, 250, 0.15);
                    border-radius: 16px;
                    overflow: hidden;
                    box-sizing: border-box;
                }}
                #mynetwork {{
                    flex: 6.8;
                    width: 68%;
                    height: 100%;
                }}
                #detail-drawer {{
                    flex: 3.2;
                    width: 32%;
                    height: 100%;
                    background: rgba(13, 13, 23, 0.95);
                    border-left: 1px solid rgba(167, 139, 250, 0.15);
                    padding: 1.2rem;
                    box-sizing: border-box;
                    display: flex;
                    flex-direction: column;
                    color: #e4e4e7;
                    overflow-y: auto;
                    box-shadow: -5px 0 20px rgba(0,0,0,0.5);
                }}
                #drawer-header {{
                    font-size: 1rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 1rem;
                    padding-bottom: 0.5rem;
                    border-bottom: 1px solid rgba(167, 139, 250, 0.2);
                    background: linear-gradient(135deg, #c084fc, #818cf8);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                .drawer-section {{
                    margin-bottom: 0.85rem;
                }}
                .section-label {{
                    font-size: 0.72rem;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    color: #71717a;
                    font-weight: 600;
                    margin-bottom: 0.25rem;
                }}
                .section-val {{
                    font-size: 0.88rem;
                    color: #e4e4e7;
                    font-weight: 400;
                }}
                .tag {{
                    display: inline-block;
                    padding: 0.2rem 0.6rem;
                    border-radius: 6px;
                    font-size: 0.72rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    margin-top: 0.35rem;
                }}
                .tag-agent {{ background: rgba(167, 139, 250, 0.15); color: #c084fc; border: 1px solid rgba(167, 139, 250, 0.3); }}
                .tag-llm {{ background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); }}
                .tag-memory {{ background: rgba(96, 165, 250, 0.15); color: #60a5fa; border: 1px solid rgba(96, 165, 250, 0.3); }}
                .tag-graph {{ background: rgba(251, 113, 133, 0.15); color: #fb7185; border: 1px solid rgba(251, 113, 133, 0.3); }}
                .tag-resilience {{ background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }}
                .tag-user {{ background: rgba(244, 114, 182, 0.15); color: #f472b6; border: 1px solid rgba(244, 114, 182, 0.3); }}
                .tag-chunk {{ background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }}
                .tag-entity {{ background: rgba(129, 140, 248, 0.15); color: #a5b4fc; border: 1px solid rgba(129, 140, 248, 0.3); }}
                
                .prop-box {{
                    background: rgba(15, 15, 24, 0.6);
                    border: 1px solid rgba(63, 63, 80, 0.4);
                    border-radius: 8px;
                    padding: 0.6rem 0.8rem;
                    font-size: 0.8rem;
                    line-height: 1.4;
                    color: #d4d4d8;
                    max-height: 180px;
                    overflow-y: auto;
                    word-break: break-word;
                }}
                .use-btn {{
                    background: linear-gradient(135deg, #c084fc 0%, #6366f1 100%);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 0.55rem 1rem;
                    font-size: 0.82rem;
                    font-weight: 600;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.4rem;
                    margin-top: 1rem;
                    transition: all 0.25s ease;
                    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
                }}
                .use-btn:hover {{
                    box-shadow: 0 6px 18px rgba(99, 102, 241, 0.5);
                    transform: translateY(-1px);
                }}
                .use-btn:active {{
                    transform: translateY(0);
                }}
                
                #toast {{
                    visibility: hidden;
                    min-width: 240px;
                    background-color: #10b981;
                    color: #fff;
                    text-align: center;
                    border-radius: 8px;
                    padding: 0.65rem;
                    position: fixed;
                    z-index: 1000;
                    bottom: 20px;
                    right: 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.45);
                    opacity: 0;
                    transition: opacity 0.3s, visibility 0.3s;
                }}
                #toast.show {{
                    visibility: visible;
                    opacity: 1;
                }}
            </style>
        </head>
        <body>
        <div id="container-split">
            <div id="mynetwork"></div>
            <div id="detail-drawer">
                <div id="drawer-header">Neural Details</div>
                <div id="drawer-body">
                    <p style="color: #71717a; font-size: 0.85rem; font-style: italic; margin-top: 0;">Click on a node or connection path in the graph to view properties.</p>
                </div>
            </div>
        </div>
        <div id="toast">Prompt copied! Paste it in the chat box on the left.</div>

        <script type="text/javascript">
            window.onerror = function(message, source, lineno, colno, error) {{
                console.error("IFRAME ERROR: " + message + " at " + source + ":" + lineno + ":" + colno);
                return false;
            }};
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
                    size: 20,
                    font: {{
                        color: '#ffffff',
                        size: 13,
                        face: 'Outfit, sans-serif'
                    }},
                    borderWidth: 2,
                    shadow: true
                }},
                edges: {{
                    width: 2,
                    color: {{ color: 'rgba(129, 140, 248, 0.4)', highlight: '#c084fc' }},
                    font: {{
                        color: '#a5b4fc',
                        size: 10,
                        align: 'horizontal',
                        background: '#040408'
                    }},
                    arrows: {{
                        to: {{ enabled: true, scaleFactor: 0.7 }}
                    }},
                    smooth: {{
                        type: 'cubicBezier',
                        forceDirection: 'none',
                        roundness: 0.4
                    }}
                }},
                groups: {{
                    Agent: {{ color: {{ background: '#c084fc', border: '#a78bfa' }} }},
                    LLM: {{ color: {{ background: '#34d399', border: '#059669' }} }},
                    Memory: {{ color: {{ background: '#60a5fa', border: '#2563eb' }} }},
                    GraphStore: {{ color: {{ background: '#fb7185', border: '#e11d48' }} }},
                    Resilience: {{ color: {{ background: '#fbbf24', border: '#d97706' }} }},
                    User: {{ color: {{ background: '#f472b6', border: '#db2777' }} }},
                    Entity: {{ color: {{ background: '#818cf8', border: '#6366f1' }} }},
                    Chunk: {{ color: {{ background: '#94a3b8', border: '#475569' }} }}
                }},
                physics: {{
                    stabilization: false,
                    barnesHut: {{
                        gravitationalConstant: -3500,
                        springConstant: 0.04,
                        springLength: 120
                    }}
                }},
                interaction: {{
                    hover: true
                }}
            }};
            var network = new vis.Network(container, data, options);
            
            var drawerBody = document.getElementById('drawer-body');
            var drawerHeader = document.getElementById('drawer-header');
            
            function renderProperties(props) {{
                if (!props || Object.keys(props).length === 0) {{
                    return '<p style="color: #71717a; font-style: italic; font-size: 0.8rem;">None</p>';
                }}
                var html = '<div style="display:flex; flex-direction:column; gap:0.45rem;">';
                for (var key in props) {{
                    if (props.hasOwnProperty(key)) {{
                        html += '<div>';
                        html += '<div class="section-label">' + key + '</div>';
                        if (key === 'text') {{
                            html += '<div class="prop-box" style="white-space: pre-wrap;">' + props[key] + '</div>';
                        }} else {{
                            html += '<div class="section-val">' + props[key] + '</div>';
                        }}
                        html += '</div>';
                    }}
                }}
                html += '</div>';
                return html;
            }}

            function getTagClass(group) {{
                var g = (group || '').toLowerCase();
                if (g.includes('agent')) return 'tag-agent';
                if (g.includes('llm')) return 'tag-llm';
                if (g.includes('memory')) return 'tag-memory';
                if (g.includes('graph')) return 'tag-graph';
                if (g.includes('resilience')) return 'tag-resilience';
                if (g.includes('user')) return 'tag-user';
                if (g.includes('chunk')) return 'tag-chunk';
                return 'tag-entity';
            }}
            
            function selectNodeHandler(nodeId) {{
                var node = nodes.get(nodeId);
                if (!node) return;
                
                drawerHeader.innerText = "Node Details";
                
                var tagClass = getTagClass(node.group);
                var labelName = node.label || 'Unnamed Node';
                var groupName = node.group || 'Entity';
                
                // Formulate prompt
                var promptText = "Tell me more about " + labelName;
                if (node.properties) {{
                    if (node.properties.text) {{
                        promptText = "From the document chunk details, tell me more about: " + node.properties.text.substring(0, 150).replace(/"/g, '') + "...";
                    }} else if (node.properties.Description) {{
                        promptText = "Tell me about " + labelName + ": " + node.properties.Description;
                    }}
                }}
                
                var base64Prompt = btoa(unescape(encodeURIComponent(promptText)));
                
                var html = '';
                html += '<div class="drawer-section">';
                html += '<div class="section-label">Node Name</div>';
                html += '<div class="section-val" style="font-weight:600; font-size:0.95rem;">' + labelName + '</div>';
                html += '<span class="tag ' + tagClass + '">' + groupName + '</span>';
                html += '</div>';
                
                html += '<div class="drawer-section">';
                html += '<div class="section-label">Attributes</div>';
                html += renderProperties(node.properties);
                html += '</div>';
                
                html += '<button class="use-btn" onclick="triggerUseInChat(\\\'' + base64Prompt + '\\\')">';
                html += '<span>Use in Chat 💬</span>';
                html += '</button>';
                
                drawerBody.innerHTML = html;
            }}
            
            function selectEdgeHandler(edgeId) {{
                var edge = edges.get(edgeId);
                if (!edge) return;
                
                drawerHeader.innerText = "Connection Details";
                
                var fromNode = nodes.get(edge.from);
                var toNode = nodes.get(edge.to);
                var fromName = fromNode ? fromNode.label : 'Node ' + edge.from;
                var toName = toNode ? toNode.label : 'Node ' + edge.to;
                
                var relType = edge.label || 'RELATED';
                var promptText = "Explain the connection: " + fromName + " —[" + relType + "]—> " + toName;
                if (edge.properties && Object.keys(edge.properties).length > 0) {{
                    var propsStr = JSON.stringify(edge.properties);
                    promptText += " with properties " + propsStr;
                }}
                
                var base64Prompt = btoa(unescape(encodeURIComponent(promptText)));
                
                var html = '';
                html += '<div class="drawer-section">';
                html += '<div class="section-label">Source Node</div>';
                html += '<div class="section-val" style="font-weight:600;">' + fromName + '</div>';
                html += '</div>';
                
                html += '<div class="drawer-section">';
                html += '<div class="section-label">Relationship Path</div>';
                html += '<div class="section-val" style="color:#c084fc; font-weight:600;">→ ' + relType + ' →</div>';
                html += '</div>';
                
                html += '<div class="drawer-section">';
                html += '<div class="section-label">Target Node</div>';
                html += '<div class="section-val" style="font-weight:600;">' + toName + '</div>';
                html += '</div>';
                
                html += '<div class="drawer-section">';
                html += '<div class="section-label">Attributes</div>';
                html += renderProperties(edge.properties);
                html += '</div>';
                
                html += '<button class="use-btn" onclick="triggerUseInChat(\\\'' + base64Prompt + '\\\')">';
                html += '<span>Use in Chat 💬</span>';
                html += '</button>';
                
                drawerBody.innerHTML = html;
            }}
            
            network.on("selectNode", function(params) {{
                if (params.nodes.length > 0) {{
                    selectNodeHandler(params.nodes[0]);
                }}
            }});
            
            network.on("selectEdge", function(params) {{
                if (params.nodes.length === 0 && params.edges.length > 0) {{
                    selectEdgeHandler(params.edges[0]);
                }}
            }});
            
            network.on("deselectNode", function(params) {{
                resetDrawer();
            }});
            
            network.on("deselectEdge", function(params) {{
                resetDrawer();
            }});
            
            function resetDrawer() {{
                drawerHeader.innerText = "Neural Details";
                drawerBody.innerHTML = '<p style="color: #71717a; font-size: 0.85rem; font-style: italic; margin-top: 0;">Click on a node or connection path in the graph to view properties.</p>';
            }}
            
            function triggerUseInChat(base64Text) {{
                var promptText = decodeURIComponent(escape(atob(base64Text)));
                
                navigator.clipboard.writeText(promptText).then(function() {{
                    console.log("INAYAT: Copied to clipboard successfully.");
                }}, function(err) {{
                    console.error("INAYAT: Clipboard copy failed:", err);
                }});
                
                try {{
                    var parentDoc = window.parent.document;
                    var chatInput = parentDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
                    if (chatInput) {{
                        console.log("INAYAT: Found parent chat input.");
                        var lastValue = chatInput.value;
                        chatInput.value = promptText;
                        
                        var inputEvent = new Event('input', {{ bubbles: true }});
                        var tracker = chatInput._valueTracker;
                        if (tracker) {{
                            tracker.setValue(lastValue);
                        }}
                        chatInput.dispatchEvent(inputEvent);
                        
                        setTimeout(function() {{
                            var submitButton = parentDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
                            if (submitButton) {{
                                console.log("INAYAT: Clicking parent submit button.");
                                submitButton.click();
                            }} else {{
                                console.log("INAYAT: Parent submit button not found, dispatching Enter.");
                                var enterEvent = new KeyboardEvent('keydown', {{
                                    key: 'Enter',
                                    code: 'Enter',
                                    keyCode: 13,
                                    which: 13,
                                    bubbles: true,
                                    cancelable: true
                                }});
                                chatInput.dispatchEvent(enterEvent);
                            }}
                        }}, 150);
                        
                        var toast = document.getElementById('toast');
                        toast.innerText = "Synced to Agent Chat! 💬";
                        toast.className = 'show';
                        setTimeout(function(){{ toast.className = toast.className.replace('show', ''); }}, 3000);
                    }} else {{
                        console.error("INAYAT: Parent chat input not found.");
                        var toast = document.getElementById('toast');
                        toast.innerText = "Synced to clipboard (Chat input not found)!";
                        toast.className = 'show';
                        setTimeout(function(){{ toast.className = toast.className.replace('show', ''); }}, 3000);
                    }}
                }} catch (e) {{
                    console.error("INAYAT: Direct parent access failed:", e);
                    var toast = document.getElementById('toast');
                    toast.innerText = "Synced to clipboard (Parent access blocked)!";
                    toast.className = 'show';
                    setTimeout(function(){{ toast.className = toast.className.replace('show', ''); }}, 3000);
                }}
            }}
        </script>
        </body>
        </html>
        """
        st.components.v1.html(html_content, height=520)

    # ── User Input Query Resolution (Executed in rerun / background) ────
    # In Streamlit's new layout, we check if there's a new query appended to state that needs processing
    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        user_prompt = st.session_state.messages[-1]["content"]
        
        # Save memory
        from core.memory import add_memory
        add_memory(st.session_state.user_id, user_prompt)
        
        # Get memory context
        mem_lines = _fetch_memories(st.session_state.user_id)
        memory_ctx = "\n".join(f"• {m}" for m in mem_lines) if mem_lines else ""
        
        # Render a temporary placeholder thinking text in the left column
        with col_left:
            st.markdown("<div class='thinking'>Thinking…</div>", unsafe_allow_html=True)
        
        # Query agent
        from core.agent import query as agent_query
        answer = agent_query(user_prompt, user_id=st.session_state.user_id, memory_context=memory_ctx)
        
        # Append answer
        st.session_state.messages.append({"role": "assistant", "content": answer})
        
        # Keep window clean
        if len(st.session_state.messages) > 20:
            st.session_state.messages = st.session_state.messages[-20:]
            
        st.rerun()


if __name__ == "__main__":
    main()
