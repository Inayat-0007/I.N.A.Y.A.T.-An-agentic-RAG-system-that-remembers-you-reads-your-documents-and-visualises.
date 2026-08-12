# -*- coding: utf-8 -*-
"""I.N.A.Y.A.T. — Main Streamlit Application.

Intelligent Neural Architecture for Yielding Agentic Thinking.
An AI agent that remembers, reads your documents, and shows its knowledge graph.

Launch:
    streamlit run app.py
"""

import time
import logging
import uuid
import streamlit as st
from typing import Dict, List

# Unique per Streamlit worker process — used to drop stale breaker widget state.
_APP_BOOT_TOKEN = uuid.uuid4().hex

# ── Bootstrap (must happen before any other core import) ──────────────
from core.startup import enforce_critical_env_or_exit, run_startup

enforce_critical_env_or_exit()
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
st.markdown(
    """
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

/* ── Hero Section ───────────────────────────── */
.hero-section {
    position: relative;
    margin: 0 0 1.75rem 0;
    padding: 1.6rem 2rem 1.4rem;
    border-radius: 20px;
    background: linear-gradient(
        145deg,
        rgba(20, 18, 42, 0.72) 0%,
        rgba(10, 10, 24, 0.58) 100%
    );
    border: 1px solid rgba(167, 139, 250, 0.16);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow:
        0 8px 32px rgba(0, 0, 0, 0.38),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    overflow: hidden;
    animation: fadeUp 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}
.hero-section::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(192, 132, 252, 0.55) 35%,
        rgba(129, 140, 248, 0.55) 65%,
        transparent 100%
    );
}
.hero-section::after {
    content: '';
    position: absolute;
    top: -40%; right: -15%;
    width: 55%; height: 180%;
    background: radial-gradient(
        ellipse at center,
        rgba(99, 102, 241, 0.09) 0%,
        transparent 68%
    );
    pointer-events: none;
}
.hero-inner {
    position: relative;
    z-index: 1;
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #c4b5fd;
    margin-bottom: 0.7rem;
    padding: 0.32rem 0.8rem;
    border-radius: 100px;
    background: rgba(167, 139, 250, 0.1);
    border: 1px solid rgba(167, 139, 250, 0.22);
}
.hero-eyebrow-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #34d399;
    box-shadow: 0 0 8px rgba(52, 211, 153, 0.55);
    flex-shrink: 0;
    animation: pulse 2.2s ease-in-out infinite;
}
.hero-title {
    background: linear-gradient(
        120deg,
        #f3e8ff 0%,
        #d8b4fe 18%,
        #c084fc 38%,
        #818cf8 62%,
        #6366f1 82%,
        #a5b4fc 100%
    );
    background-size: 200% auto;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: clamp(2rem, 4.5vw, 3.15rem);
    font-weight: 800;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 0.06em;
    line-height: 1.08;
    margin: 0 0 0.55rem 0;
    filter: drop-shadow(0 2px 14px rgba(129, 140, 248, 0.28));
}
.hero-title-sep {
    -webkit-text-fill-color: rgba(192, 132, 252, 0.55);
    font-weight: 500;
}
.hero-sub {
    color: #c8c8d0;
    font-size: clamp(0.88rem, 1.8vw, 1.02rem);
    font-weight: 400;
    line-height: 1.65;
    max-width: 54ch;
    margin: 0;
    letter-spacing: 0.01em;
}
.hero-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 1rem;
}
.hero-tag {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.7rem;
    font-weight: 500;
    color: #b0b0b8;
    padding: 0.26rem 0.62rem;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.07);
    letter-spacing: 0.02em;
}
@media (max-width: 640px) {
    .hero-section {
        padding: 1.2rem 1.15rem 1.05rem;
        margin-bottom: 1.25rem;
        border-radius: 16px;
    }
    .hero-title { letter-spacing: 0.04em; }
}

/* ── Sidebar (2026 glass panel) ─────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(165deg, #0a0914 0%, #040408 55%, #030306 100%);
    border-right: 1px solid rgba(167, 139, 250, 0.14);
    box-shadow: 4px 0 32px rgba(0, 0, 0, 0.45);
}
section[data-testid="stSidebar"] > div {
    background: transparent !important;
}
[data-testid="stSidebarContent"] {
    padding: 0.85rem 0.9rem 1.25rem !important;
    animation: fadeUp 0.38s cubic-bezier(0.16, 1, 0.3, 1);
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.35rem !important;
}
[data-testid="stSidebar"] hr {
    border: none !important;
    height: 1px !important;
    margin: 0.65rem 0 !important;
    background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(167, 139, 250, 0.22) 35%,
        rgba(129, 140, 248, 0.22) 65%,
        transparent 100%
    ) !important;
}

/* Brand header card */
.sidebar-header {
    position: relative;
    padding: 1.05rem 1rem 0.95rem;
    margin-bottom: 0.15rem;
    border-radius: 16px;
    background: linear-gradient(
        145deg,
        rgba(20, 18, 42, 0.72) 0%,
        rgba(10, 10, 24, 0.58) 100%
    );
    border: 1px solid rgba(167, 139, 250, 0.16);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow:
        0 6px 24px rgba(0, 0, 0, 0.32),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
    overflow: hidden;
}
.sidebar-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(192, 132, 252, 0.5) 40%,
        rgba(129, 140, 248, 0.5) 60%,
        transparent 100%
    );
}
.sidebar-header::after {
    content: '';
    position: absolute;
    top: -30%; right: -20%;
    width: 60%; height: 140%;
    background: radial-gradient(
        ellipse at center,
        rgba(99, 102, 241, 0.08) 0%,
        transparent 70%
    );
    pointer-events: none;
}
.sidebar-brand {
    position: relative;
    z-index: 1;
    background: linear-gradient(
        120deg,
        #f3e8ff 0%,
        #d8b4fe 20%,
        #c084fc 40%,
        #818cf8 65%,
        #6366f1 85%,
        #a5b4fc 100%
    );
    background-size: 200% auto;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.55rem;
    font-weight: 800;
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: 0.05em;
    line-height: 1.15;
    margin: 0;
    filter: drop-shadow(0 2px 10px rgba(129, 140, 248, 0.25));
}
.sidebar-sub {
    position: relative;
    z-index: 1;
    color: #9ca3af;
    font-size: 0.72rem;
    font-weight: 400;
    line-height: 1.55;
    margin: 0.45rem 0 0 0;
    letter-spacing: 0.02em;
}
.sidebar-eyebrow {
    position: relative;
    z-index: 1;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #c4b5fd;
    margin-bottom: 0.5rem;
    padding: 0.28rem 0.65rem;
    border-radius: 100px;
    background: rgba(167, 139, 250, 0.1);
    border: 1px solid rgba(167, 139, 250, 0.2);
}
.sidebar-eyebrow-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: #34d399;
    box-shadow: 0 0 6px rgba(52, 211, 153, 0.55);
    animation: pulse 2.2s ease-in-out infinite;
}

/* Section headers */
.sidebar-section-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0.15rem 0 0.45rem 0;
    padding: 0.15rem 0;
}
.sidebar-section-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px; height: 28px;
    border-radius: 8px;
    font-size: 0.85rem;
    background: rgba(167, 139, 250, 0.1);
    border: 1px solid rgba(167, 139, 250, 0.18);
    flex-shrink: 0;
}
.sidebar-section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #e4e4e7;
}

/* Health status pills */
.health-grid {
    display: flex;
    flex-direction: column;
    gap: 0.42rem;
    margin-top: 0.15rem;
}
.health-pill {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.55rem 0.75rem;
    border-radius: 10px;
    font-size: 0.8rem;
    font-weight: 500;
    background: rgba(12, 12, 22, 0.65);
    border: 1px solid rgba(167, 139, 250, 0.12);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.22);
    transition:
        border-color 0.18s cubic-bezier(0.16, 1, 0.3, 1),
        box-shadow 0.18s cubic-bezier(0.16, 1, 0.3, 1),
        transform 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}
.health-pill:hover {
    border-color: rgba(167, 139, 250, 0.28);
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.12);
    transform: translateX(2px);
}
.health-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    transition: box-shadow 0.18s ease;
}
.health-dot--up {
    background: #34d399;
    box-shadow: 0 0 8px rgba(52, 211, 153, 0.55);
    animation: pulse 2.2s ease-in-out infinite;
}
.health-dot--down {
    background: #f87171;
    box-shadow: 0 0 8px rgba(248, 113, 113, 0.45);
}
.health-dot--warn {
    background: #fbbf24;
    box-shadow: 0 0 8px rgba(251, 191, 36, 0.4);
}
.health-dot--idle {
    background: #71717a;
    box-shadow: none;
}
.health-pill-label {
    color: #d4d4d8;
    flex: 1 1 auto;
    min-width: 0;
    font-family: 'Outfit', sans-serif;
    letter-spacing: 0.01em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.health-pill-status {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 0.18rem 0.5rem;
    border-radius: 100px;
    flex-shrink: 0;
    margin-left: auto;
    white-space: nowrap;
}
.health-pill-status--up {
    color: #34d399;
    background: rgba(52, 211, 153, 0.1);
    border: 1px solid rgba(52, 211, 153, 0.22);
}
.health-pill-status--down {
    color: #f87171;
    background: rgba(248, 113, 113, 0.1);
    border: 1px solid rgba(248, 113, 113, 0.22);
}
.health-pill-status--warn {
    color: #fbbf24;
    background: rgba(251, 191, 36, 0.1);
    border: 1px solid rgba(251, 191, 36, 0.22);
}
.health-pill-status--idle {
    color: #a1a1aa;
    background: rgba(161, 161, 170, 0.08);
    border: 1px solid rgba(161, 161, 170, 0.15);
}

/* Sidebar-scoped inputs & upload */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: rgba(10, 10, 20, 0.55) !important;
    border: 1px dashed rgba(167, 139, 250, 0.28) !important;
    border-radius: 12px !important;
    padding: 0.55rem 0.65rem !important;
    transition:
        border-color 0.18s cubic-bezier(0.16, 1, 0.3, 1),
        background 0.18s ease,
        box-shadow 0.18s ease !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"]:hover {
    border-color: rgba(167, 139, 250, 0.45) !important;
    background: rgba(15, 15, 28, 0.65) !important;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.08) !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
    padding: 0.35rem !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] small {
    color: #71717a !important;
    font-size: 0.72rem !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
    background: linear-gradient(135deg, #a78bfa, #6366f1) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.4rem 1rem !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    transition:
        box-shadow 0.18s cubic-bezier(0.16, 1, 0.3, 1),
        transform 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {
    box-shadow: 0 0 14px rgba(167, 139, 250, 0.35) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stSidebar"] div[data-baseweb="input"] {
    background: rgba(8, 8, 15, 0.85) !important;
    border: 1px solid rgba(167, 139, 250, 0.18) !important;
    border-radius: 10px !important;
    transition:
        border-color 0.18s ease,
        box-shadow 0.18s ease !important;
}
[data-testid="stSidebar"] div[data-baseweb="input"]:focus-within {
    border-color: #818cf8 !important;
    box-shadow: 0 0 10px rgba(129, 140, 248, 0.25) !important;
}
[data-testid="stSidebar"] button[kind="secondary"] {
    background: rgba(12, 12, 22, 0.75) !important;
    border: 1px solid rgba(167, 139, 250, 0.18) !important;
    border-radius: 10px !important;
    font-size: 0.82rem !important;
    transition:
        border-color 0.18s cubic-bezier(0.16, 1, 0.3, 1),
        box-shadow 0.18s cubic-bezier(0.16, 1, 0.3, 1),
        transform 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    border-color: rgba(167, 139, 250, 0.4) !important;
    color: #c4b5fd !important;
    box-shadow: 0 0 12px rgba(167, 139, 250, 0.15) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label {
    color: #a1a1aa !important;
    font-size: 0.82rem !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: rgba(10, 10, 20, 0.5) !important;
    border: 1px solid rgba(167, 139, 250, 0.12) !important;
    border-radius: 10px !important;
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
""",
    unsafe_allow_html=True,
)


# ── Session state init ────────────────────────────────────────────────


def _reset_breaker_widgets_on_server_restart() -> None:
    """Drop stale Force Fail checkbox state after a Streamlit worker restart."""
    if st.session_state.get("_inayat_boot_token") == _APP_BOOT_TOKEN:
        return
    st.session_state["_inayat_boot_token"] = _APP_BOOT_TOKEN
    for key in ("resilience_fail_mem0", "resilience_fail_neo4j"):
        st.session_state.pop(key, None)


def _init_state() -> None:
    """Initialise all session state keys once."""
    _reset_breaker_widgets_on_server_restart()
    # Pre-populate user_id from query params if available
    default_user = st.query_params.get("user", "")
    if default_user and f"messages_{default_user}" not in st.session_state:
        st.session_state[f"messages_{default_user}"] = []
    defaults = {
        "messages": (
            st.session_state.get(f"messages_{default_user}", []) if default_user else []
        ),
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


# ── Sidebar helpers ───────────────────────────────────────────────────


def _sidebar_section(icon: str, title: str) -> None:
    """Render a styled sidebar section header."""
    st.markdown(
        f"<div class='sidebar-section-header'>"
        f"<span class='sidebar-section-icon'>{icon}</span>"
        f"<span class='sidebar-section-title'>{title}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _health_pill_html(status: str, label: str) -> str:
    """Convert emoji status string to a modern health pill."""
    if "🟢" in status or "Connected" in status:
        dot_cls, status_cls, text = "health-dot--up", "health-pill-status--up", "Connected"
    elif "🔴" in status or "Unreachable" in status or "Forced" in status:
        dot_cls, status_cls, text = "health-dot--down", "health-pill-status--down", status.replace("🟢 ", "").replace("🔴 ", "").replace("🟡 ", "").replace("⚪ ", "")
    elif "🟡" in status or "Degraded" in status:
        dot_cls, status_cls, text = "health-dot--warn", "health-pill-status--warn", "Degraded"
    else:
        dot_cls, status_cls, text = "health-dot--idle", "health-pill-status--idle", status.replace("🟢 ", "").replace("🔴 ", "").replace("🟡 ", "").replace("⚪ ", "")
    return (
        f"<div class='health-pill'>"
        f"<span class='health-dot {dot_cls}' aria-hidden='true'></span>"
        f"<span class='health-pill-label'>{label}</span>"
        f"<span class='health-pill-status {status_cls}'>{text}</span>"
        f"</div>"
    )


# ── Sidebar ───────────────────────────────────────────────────────────


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class='sidebar-header'>
                <div class='sidebar-eyebrow'>
                    <span class='sidebar-eyebrow-dot' aria-hidden='true'></span>
                    Agent Console
                </div>
                <div class='sidebar-brand'>I.N.A.Y.A.T.</div>
                <p class='sidebar-sub'>Intelligent Neural Architecture for Yielding Agentic Thinking</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # User profile
        _sidebar_section("👤", "User Profile")
        name = st.text_input(
            "Your name",
            value=st.session_state.user_id,
            placeholder="e.g. Moham",
            label_visibility="collapsed",
        )
        if name != st.session_state.user_id:
            from core.identity import InvalidUserId, UserId

            try:
                UserId.parse(name)
            except InvalidUserId as exc:
                st.error(str(exc))
                name = st.session_state.user_id or "default"
            if st.session_state.user_id:
                st.session_state[f"messages_{st.session_state.user_id}"] = (
                    st.session_state.messages
                )
            st.session_state.user_id = name
            st.query_params["user"] = name
            st.session_state.messages = st.session_state.get(f"messages_{name}", [])
            st.rerun()

        st.markdown("---")

        # Document Ingestion
        _sidebar_section("📂", "Ingest Documents")
        uploaded_files = st.file_uploader(
            "Upload PDFs or TXT files",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        from core.ingest import (
            build_index,
            get_index_status,
            list_user_documents,
            save_uploads,
            unindexed_document_names,
        )

        on_disk = list_user_documents(st.session_state.user_id)
        if on_disk:
            st.caption("On disk:")
            for row in on_disk:
                kb = row["size"] / 1024
                st.caption(f"• {row['name']} ({kb:.1f} KB)")

        pending_names = unindexed_document_names(st.session_state.user_id)
        already_indexed = [
            row["name"] for row in on_disk if row["name"] not in pending_names
        ]
        if already_indexed:
            st.caption("Already indexed (unchanged): " + ", ".join(already_indexed))
        auto_key = tuple(pending_names)
        if (
            pending_names
            and not uploaded_files
            and st.session_state.get("_ingest_auto_key") != auto_key
        ):
            st.session_state._ingest_auto_key = auto_key
            st.info("Saved files are not indexed yet: " + ", ".join(pending_names))
            try:
                with st.spinner(
                    f"Indexing {len(pending_names)} pending file(s): {', '.join(pending_names)}"
                ):
                    result = build_index(
                        st.session_state.user_id, only_files=pending_names
                    )
                if result is None:
                    err = get_index_status(st.session_state.user_id).get("error")
                    st.error(err or "Index build returned no index. Check logs.")
                else:
                    st.success("Graph index updated!")
                    st.rerun()
            except Exception as exc:
                st.error(f"Indexing failed: {exc}")

        if uploaded_files:
            payloads = [(f.name, f.getbuffer().tobytes()) for f in uploaded_files]
            try:
                saved = save_uploads(
                    st.session_state.user_id, payloads, overwrite=False
                )
            except Exception as exc:
                st.error(str(exc))
                saved = []

            if saved:
                st.success("Saved: " + ", ".join(saved))
            to_index = saved or (
                unindexed_document_names(st.session_state.user_id)
                if uploaded_files
                else []
            )
            if to_index:
                job = get_index_status(st.session_state.user_id)
                if job.get("status") == "building":
                    st.info("Indexing already in progress — files are on disk.")
                else:
                    names = ", ".join(to_index)
                    try:
                        with st.spinner(
                            f"Indexing {len(to_index)} file(s): {names}"
                        ):
                            result = build_index(
                                st.session_state.user_id, only_files=to_index
                            )
                        if result is None:
                            err = get_index_status(st.session_state.user_id).get("error")
                            st.error(err or "Index build returned no index. Check logs.")
                        else:
                            st.success("Graph index updated!")
                            st.rerun()
                    except Exception as exc:
                        st.error(f"Indexing failed: {exc}")
            elif uploaded_files:
                st.caption("Those files are already saved and indexed.")

        st.markdown("---")

        # Health panel
        _sidebar_section("🛡️", "Service Health")
        if st.button("🔄 Refresh", use_container_width=True):
            with st.spinner("Probing services…"):
                monitor = _get_health_monitor()
                st.session_state.health = monitor.run_all()

        h = st.session_state.health

        # Override health display if forced failures are active
        import core.memory as mem
        import core.graph_store as gs
        from core.resilience import clear_stale_forced_breakers

        clear_stale_forced_breakers()
        _reset_breaker_widgets_on_server_restart()

        is_mem_forced = getattr(mem._cb, "forced_open", False)
        is_graph_forced = getattr(gs._cb, "forced_open", False)

        pills = []
        for svc, label in [
            ("gemini", "Gemini LLM"),
            ("mem0", "Mem0 Memory"),
            ("neo4j", "Neo4j Graph"),
        ]:
            status = h.get(svc, "⚪ Unknown")
            if svc == "mem0" and is_mem_forced:
                status = "🔴 Forced Fail"
            elif svc == "neo4j" and is_graph_forced:
                status = "🔴 Forced Fail"
            pills.append(_health_pill_html(status, label))

        st.markdown(
            f"<div class='health-grid'>{''.join(pills)}</div>",
            unsafe_allow_html=True,
        )

        # Startup warnings
        for w in st.session_state.startup_warnings:
            st.warning(w, icon="⚠️")

        # Resilience Testing Panel (demo mode only)
        st.markdown("---")
        _sidebar_section("🧪", "Resilience Testing")

        from core.resilience import DemoModeRequired, set_breaker_forced_open
        from core.settings import get_settings

        demo_mode = get_settings().demo_mode
        if not demo_mode:
            # Disabled toggles must mirror breaker state (no stale checked UI).
            st.session_state["resilience_fail_mem0"] = is_mem_forced
            st.session_state["resilience_fail_neo4j"] = is_graph_forced

        fail_mem0 = st.checkbox(
            "🔥 Force Fail Mem0",
            value=is_mem_forced,
            key="resilience_fail_mem0",
            disabled=not demo_mode,
        )
        if demo_mode and fail_mem0 != is_mem_forced:
            try:
                set_breaker_forced_open(mem._cb, fail_mem0, service="Mem0")
            except DemoModeRequired as exc:
                st.error(str(exc))
            else:
                st.rerun()

        fail_neo4j = st.checkbox(
            "🔥 Force Fail Neo4j",
            value=is_graph_forced,
            key="resilience_fail_neo4j",
            disabled=not demo_mode,
        )
        if demo_mode and fail_neo4j != is_graph_forced:
            try:
                set_breaker_forced_open(gs._cb, fail_neo4j, service="Neo4j")
            except DemoModeRequired as exc:
                st.error(str(exc))
            else:
                st.rerun()

        if not demo_mode:
            st.caption("Set INAYAT_DEMO_MODE=true to enable circuit breaker demo toggles.")
        elif fail_mem0 or fail_neo4j:
            st.warning(
                "Circuit breaker(s) forced OPEN. Systems running in degraded mode."
            )

        st.markdown("---")

        # Actions
        _sidebar_section("⚙️", "Actions")
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
        st.markdown(
            """
        <div style="padding: 1rem 0; margin-top: 0.5rem; animation: fadeUp 0.4s ease-out; text-align: center;">
            <div style="background: linear-gradient(135deg, rgba(167, 139, 250, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%); 
                        border: 1px solid rgba(167, 139, 250, 0.18); 
                        padding: 3.5rem 2rem; border-radius: 24px; max-width: 850px; margin: 0 auto;
                        box-shadow: 0 20px 40px rgba(0,0,0,0.5); backdrop-filter: blur(16px);">
        """,
            unsafe_allow_html=True,
        )

        col_img1, col_img2, col_img3 = st.columns([1, 1, 1])
        with col_img2:
            st.markdown(
                "<div style='font-size:4rem;text-align:center;'>🧠</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            """
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
        """,
            unsafe_allow_html=True,
        )

        col_space1, col_input, col_space2 = st.columns([1, 3, 1])
        with col_input:
            name_input = st.text_input(
                "Profile Name",
                placeholder="e.g. Moham",
                key="landing_name_input",
                label_visibility="collapsed",
            )
            if st.button("🚀 Enter Agentic Workspace", use_container_width=True):
                from core.identity import InvalidUserId, UserId

                if name_input.strip():
                    try:
                        UserId.parse(name_input.strip())
                    except InvalidUserId as exc:
                        st.error(str(exc))
                    else:
                        st.session_state.user_id = name_input.strip()
                        st.query_params["user"] = name_input.strip()
                        st.rerun()
                else:
                    st.warning("Please enter a name to proceed.")

        st.markdown(
            """
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
        """,
            unsafe_allow_html=True,
        )
        st.stop()

    # ── Pre-warm Knowledge Graph Index ────────────────────────────────
    if "index_warmed" not in st.session_state:
        # Do not call get_index() here — from_existing on the shared Aura
        # graph blocks the UI. Chat retrieves Chunks by user_id directly.
        st.session_state.index_warmed = True
        st.session_state.startup_warning_details = None

    # ── Sandbox warning indicator ──
    if getattr(st.session_state, "startup_warning_details", None):
        st.markdown(
            """
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.25); 
                    padding: 0.85rem 1.2rem; border-radius: 12px; margin-bottom: 1.5rem; 
                    display: flex; align-items: center; gap: 0.75rem; color: #fcd34d; font-size: 0.88rem;">
            <span>⚠️</span>
            <div>
                <strong>Sandbox Mode Active:</strong> External API credentials missing or invalid. Agent queries will fall back to direct LLM fallback and mock data structures.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # ── Header ────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-section">
            <div class="hero-inner">
                <div class="hero-eyebrow">
                    <span class="hero-eyebrow-dot" aria-hidden="true"></span>
                    Agentic RAG
                </div>
                <h1 class="hero-title" aria-label="I.N.A.Y.A.T.">
                    I<span class="hero-title-sep">.</span>N<span class="hero-title-sep">.</span>A<span class="hero-title-sep">.</span>Y<span class="hero-title-sep">.</span>A<span class="hero-title-sep">.</span>T<span class="hero-title-sep">.</span>
                </h1>
                <p class="hero-sub">
                    An agentic RAG system that remembers you, reads your documents,
                    and visualises its knowledge graph.
                </p>
                <div class="hero-tags" aria-label="Capabilities">
                    <span class="hero-tag">Persistent Memory</span>
                    <span class="hero-tag">Document RAG</span>
                    <span class="hero-tag">Knowledge Graph</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Side-by-Side Unified Workspace ────────────────────────────────────
    col_left, col_right = st.columns([5, 7], gap="medium")

    with col_left:
        st.markdown(
            "<h3 style='margin-top:0; color:#f4f4f5; font-size:1.4rem; font-weight:700;'>💬 Workspace Chat</h3>",
            unsafe_allow_html=True,
        )

        # ── Memory display ────────────────────────────────────────────────
        memories = _fetch_memories(st.session_state.user_id)
        if memories:
            with st.expander(
                f"🧠 Long-Term Memory  ({len(memories)} facts)", expanded=False
            ):
                pills = "".join(f"<span class='mem-pill'>{m}</span>" for m in memories)
                st.markdown(pills, unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # ── Chat history container ────────────────────────────────────────
        for msg in st.session_state.messages:
            _render_message(msg["role"], msg["content"])

        # ── User input ────────────────────────────────────────────────────
        if prompt := st.chat_input(
            "Ask about your documents, or tell me about yourself…"
        ):
            # Display user bubble immediately
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

    with col_right:
        st.markdown(
            "<h3 style='margin-top:0; color:#f4f4f5; font-size:1.4rem; font-weight:700;'>🕸️ Neural Architecture Graph</h3>",
            unsafe_allow_html=True,
        )

        from core.graph_store import get_visualization_data

        graph_data = get_visualization_data(st.session_state.user_id)

        import json

        vis_nodes = []
        node_details = {}
        for node in graph_data["nodes"]:
            nid = node["id"]
            node_details[str(nid)] = {
                "id": nid,
                "label": node.get("label"),
                "group": node.get("group"),
                "properties": node.get("properties") or {},
            }
            vis_nodes.append(
                {
                    "id": nid,
                    "label": node.get("label"),
                    "group": node.get("group"),
                    "title": node.get("title") or node.get("label"),
                }
            )
        vis_edges = []
        edge_details = {}
        for idx, edge in enumerate(graph_data["edges"], 1):
            eid = edge.get("id") or f"e{idx}"
            edge_details[str(eid)] = {
                "id": eid,
                "from": edge.get("from"),
                "to": edge.get("to"),
                "label": edge.get("label"),
                "properties": edge.get("properties") or {},
            }
            vis_edges.append(
                {
                    "id": eid,
                    "from": edge.get("from"),
                    "to": edge.get("to"),
                    "label": edge.get("label"),
                }
            )

        nodes_js = (
            json.dumps(vis_nodes, ensure_ascii=True)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
        )
        edges_js = (
            json.dumps(vis_edges, ensure_ascii=True)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
        )
        node_details_js = (
            json.dumps(node_details, ensure_ascii=True)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
        )
        edge_details_js = (
            json.dumps(edge_details, ensure_ascii=True)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
        )

        reason = graph_data.get("mock_reason")
        if not graph_data["is_mock"]:
            is_mock_banner = "🟢 **Connected to Neo4j AuraDB** (Live Knowledge Graph)"
        elif reason == "offline":
            is_mock_banner = (
                "⚠️ **Showing System Architecture Graph** (Neo4j is unreachable)"
            )
        else:
            is_mock_banner = (
                "📄 **No documents indexed yet.** Upload a PDF to build your "
                "knowledge graph. Showing the system architecture preview until then."
            )
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
            var nodeDetails = {node_details_js};
            var edgeDetails = {edge_details_js};
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
                    hover: true,
                    selectable: true,
                    selectConnectedEdges: false
                }}
            }};
            var network = new vis.Network(container, data, options);
            
            var drawerBody = document.getElementById('drawer-body');
            var drawerHeader = document.getElementById('drawer-header');
            
            function escapeHtml(value) {{
                if (value === null || value === undefined) return '';
                return String(value)
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;');
            }}

            function renderProperties(props) {{
                if (!props || Object.keys(props).length === 0) {{
                    return '<p style="color: #71717a; font-style: italic; font-size: 0.8rem;">None</p>';
                }}
                var html = '<div style="display:flex; flex-direction:column; gap:0.45rem;">';
                for (var key in props) {{
                    if (props.hasOwnProperty(key)) {{
                        html += '<div>';
                        html += '<div class="section-label">' + escapeHtml(key) + '</div>';
                        if (key === 'text') {{
                            html += '<div class="prop-box" style="white-space: pre-wrap;">' + escapeHtml(props[key]) + '</div>';
                        }} else {{
                            html += '<div class="section-val">' + escapeHtml(props[key]) + '</div>';
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
            
            function lookupNode(nodeId) {{
                var fromMap = nodeDetails[String(nodeId)];
                if (fromMap) return fromMap;
                return nodes.get(nodeId);
            }}

            function lookupEdge(edgeId) {{
                var fromMap = edgeDetails[String(edgeId)];
                if (fromMap) return fromMap;
                return edges.get(edgeId);
            }}
            
            function selectNodeHandler(nodeId) {{
                var node = lookupNode(nodeId);
                if (!node) return;
                
                drawerHeader.innerText = "Node Details";
                
                var tagClass = getTagClass(node.group);
                var labelName = node.label || 'Unnamed Node';
                var groupName = node.group || 'Entity';
                var props = node.properties || {{}};
                
                var promptText = "Tell me more about " + labelName;
                if (props.text) {{
                    promptText = "From the document chunk details, tell me more about: " + String(props.text).substring(0, 150).replace(/"/g, '') + "...";
                }} else if (props.Description) {{
                    promptText = "Tell me about " + labelName + ": " + props.Description;
                }}
                
                var base64Prompt = btoa(unescape(encodeURIComponent(promptText)));
                
                var html = '';
                html += '<div class="drawer-section">';
                html += '<div class="section-label">Node Name</div>';
                html += '<div class="section-val" style="font-weight:600; font-size:0.95rem;">' + escapeHtml(labelName) + '</div>';
                html += '<span class="tag ' + tagClass + '">' + escapeHtml(groupName) + '</span>';
                html += '</div>';
                
                html += '<div class="drawer-section">';
                html += '<div class="section-label">Attributes</div>';
                html += renderProperties(props);
                html += '</div>';
                
                html += '<button class="use-btn" onclick="triggerUseInChat(\\\'' + base64Prompt + '\\\')">';
                html += '<span>Use in Chat 💬</span>';
                html += '</button>';
                
                drawerBody.innerHTML = html;
            }}
            
            function selectEdgeHandler(edgeId) {{
                var edge = lookupEdge(edgeId);
                if (!edge) return;
                
                drawerHeader.innerText = "Connection Details";
                
                var fromNode = lookupNode(edge.from);
                var toNode = lookupNode(edge.to);
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
                html += '<div class="section-val" style="font-weight:600;">' + escapeHtml(fromName) + '</div>';
                html += '</div>';
                
                html += '<div class="drawer-section">';
                html += '<div class="section-label">Relationship Path</div>';
                html += '<div class="section-val" style="color:#c084fc; font-weight:600;">→ ' + escapeHtml(relType) + ' →</div>';
                html += '</div>';
                
                html += '<div class="drawer-section">';
                html += '<div class="section-label">Target Node</div>';
                html += '<div class="section-val" style="font-weight:600;">' + escapeHtml(toName) + '</div>';
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
            
            network.on("click", function(params) {{
                if (params.nodes && params.nodes.length > 0) {{
                    selectNodeHandler(params.nodes[0]);
                    return;
                }}
                if (params.edges && params.edges.length > 0) {{
                    selectEdgeHandler(params.edges[0]);
                    return;
                }}
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
        st.components.v1.html(html_content, height=520, scrolling=True)

    # ── User Input Query Resolution (Executed in rerun / background) ────
    # In Streamlit's new layout, we check if there's a new query appended to state that needs processing
    if (
        len(st.session_state.messages) > 0
        and st.session_state.messages[-1]["role"] == "user"
    ):
        user_prompt = st.session_state.messages[-1]["content"]

        # Save memory
        from core.memory import add_memory, build_memory_context

        add_memory(st.session_state.user_id, user_prompt, kind="utterance")
        memory_ctx, _mem_lines = build_memory_context(
            st.session_state.user_id, user_prompt
        )

        # Render a temporary placeholder thinking text in the left column
        with col_left:
            st.markdown("<div class='thinking'>Thinking…</div>", unsafe_allow_html=True)

        # Query agent
        from core.agent import query_detailed
        from core.conversation import append_turn
        from core.observability import new_request_id, set_request_id
        from core.schemas import QueryInput

        set_request_id(new_request_id())
        result = query_detailed(
            QueryInput.from_raw(
                question=user_prompt,
                user_id=st.session_state.user_id,
                memory_context=memory_ctx,
            )
        )
        answer = result.answer
        append_turn(st.session_state.user_id, "user", user_prompt)
        append_turn(st.session_state.user_id, "assistant", answer)

        # Append answer
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "route": result.route,
                "source_count": result.source_count,
                "used_memory": result.used_memory,
                "latency_ms": result.latency_ms,
            }
        )

        # Keep window clean
        if len(st.session_state.messages) > 20:
            st.session_state.messages = st.session_state.messages[-20:]

        st.rerun()


if __name__ == "__main__":
    main()
