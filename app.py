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
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────

def _init_state() -> None:
    """Initialise all session state keys once."""
    defaults = {
        "messages": [],
        "user_id": "",
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
            st.rerun()

        st.markdown("---")

        # Health panel
        st.markdown("##### 🛡️ Service Health")
        if st.button("🔄 Refresh", use_container_width=True):
            with st.spinner("Probing services…"):
                monitor = _get_health_monitor()
                st.session_state.health = monitor.run_all()

        h = st.session_state.health
        for svc, label in [("gemini", "Gemini LLM"), ("mem0", "Mem0 Memory"), ("neo4j", "Neo4j Graph")]:
            status = h.get(svc, "⚪ Unknown")
            st.markdown(f"<div class='status-card'>{status}&ensp;{label}</div>", unsafe_allow_html=True)

        # Startup warnings
        for w in st.session_state.startup_warnings:
            st.warning(w, icon="⚠️")

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
        st.info("👈  Enter your name in the sidebar to begin.")
        st.stop()

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
