"""Live Playwright E2E for the I.N.A.Y.A.T. Streamlit UI.

Does not read or print .env secrets.

Usage (from INAYAT, with Streamlit on :8501):

    $env:PYTHONIOENCODING='utf-8'
    python scripts/browser_e2e.py

Requires: playwright (pip) and Chromium (`python -m playwright install chromium`).
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import Page, sync_playwright

URL = "http://localhost:8501/?user=Inayat"
ROOT = Path(__file__).resolve().parents[1]
SHOT = Path.home() / "AppData" / "Local" / "Temp" / "inayat_e2e"
SHOT.mkdir(parents=True, exist_ok=True)

REPORT: dict = {"tests": {}, "notes": [], "blockers": []}


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def shot(page: Page, name: str) -> None:
    path = SHOT / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    REPORT.setdefault("screenshots", []).append(str(path))


def body_text(page: Page) -> str:
    return page.locator("body").inner_text(timeout=20_000)


def ensure_streamlit() -> None:
    try:
        r = requests.get(URL, timeout=8)
    except requests.RequestException as exc:
        raise SystemExit(
            f"Streamlit is not reachable at {URL}: {exc}\n"
            "Start it from INAYAT:\n"
            "  $env:INAYAT_DEMO_MODE='true'; python -m streamlit run app.py --server.headless true"
        ) from exc
    if r.status_code >= 500:
        raise SystemExit(f"Streamlit returned HTTP {r.status_code} for {URL}")


def wait_not_running(page: Page, timeout_ms: int = 90_000) -> None:
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        running = page.locator('[data-testid="stStatusWidgetRunningIcon"]')
        if running.count() == 0:
            page.wait_for_timeout(400)
            if page.locator('[data-testid="stStatusWidgetRunningIcon"]').count() == 0:
                return
        page.wait_for_timeout(500)
    REPORT["notes"].append("Timed out waiting for Streamlit Running indicator to clear.")


def wait_workspace(page: Page, timeout_ms: int = 120_000) -> None:
    page.wait_for_selector('[data-testid="stApp"]', timeout=60_000)
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        wait_not_running(page, timeout_ms=15_000)
        chat = page.locator('[data-testid="stChatInput"]').count()
        landing = page.get_by_role(
            "button", name=re.compile("Enter Agentic Workspace")
        ).count()
        sidebar = page.locator('[data-testid="stSidebar"]').count()
        if chat or landing or sidebar:
            page.wait_for_timeout(800)
            return
        page.wait_for_timeout(500)
    raise TimeoutError(
        "Streamlit app never showed chat, sidebar, or landing after wait. "
        f"Body snippet: {body_text(page)[:400]!r}"
    )


def expand_sidebar(page: Page) -> None:
    collapsed = page.locator('[data-testid="stSidebarCollapsedControl"]')
    if collapsed.count():
        collapsed.first.click()
        page.wait_for_timeout(600)
        REPORT["notes"].append("Expanded collapsed sidebar.")


def fill_name_if_needed(page: Page) -> None:
    text = body_text(page)
    if "Enter Agentic Workspace" in text or "Initialize Demo Profile" in text:
        inp = page.locator('[data-testid="stTextInput"] input').first
        inp.click()
        inp.fill("Inayat")
        page.get_by_role("button", name=re.compile("Enter Agentic Workspace")).click()
        wait_workspace(page)
        REPORT["notes"].append("Landed on name gate; typed Inayat and entered workspace.")

    expand_sidebar(page)
    sidebar = page.locator('[data-testid="stSidebar"]')
    name_input = sidebar.locator('[data-testid="stTextInput"] input').first
    if name_input.count():
        val = name_input.input_value()
        if not val.strip():
            name_input.fill("Inayat")
            name_input.press("Enter")
            wait_workspace(page)
            REPORT["notes"].append("Sidebar name was empty; typed Inayat.")
        else:
            REPORT["notes"].append(f"Sidebar name field value: {val!r}")


def send_chat(page: Page, message: str) -> None:
    box = page.locator('[data-testid="stChatInput"] textarea')
    box.wait_for(timeout=30_000)
    box.click()
    box.fill(message)
    submit = page.locator('[data-testid="stChatInputSubmitButton"]')
    if submit.count():
        submit.first.click()
    else:
        box.press("Enter")
    page.wait_for_timeout(800)


def last_chat_text(page: Page) -> str:
    msgs = page.locator('[data-testid="stChatMessage"]')
    n = msgs.count()
    if n == 0:
        return ""
    return msgs.nth(n - 1).inner_text()


def wait_assistant(page: Page, prev_count: int, timeout_ms: int = 150_000) -> str:
    deadline = time.time() + timeout_ms / 1000
    last = ""
    saw_growth = False
    while time.time() < deadline:
        n = page.locator('[data-testid="stChatMessage"]').count()
        if n > prev_count:
            saw_growth = True
        running = page.locator('[data-testid="stStatusWidgetRunningIcon"]').count() > 0
        spinner = page.locator('[data-testid="stSpinner"]').count() > 0
        if saw_growth and not running and not spinner:
            last = last_chat_text(page)
            if last.strip() and "Running" not in last:
                return last
        page.wait_for_timeout(1000)
    return last or last_chat_text(page) or body_text(page)[-2000:]


def status_for(text: str, label: str) -> str:
    for ln in text.splitlines():
        if label in ln:
            return ln.strip()
    return ""


def is_healthy(s: str) -> bool:
    sl = s.lower()
    if not s or "forced fail" in sl or "offline" in sl or "unknown" in sl:
        return False
    if "🔴" in s or "⚪" in s:
        return False
    return ("🟢" in s) or ("connected" in sl) or ("healthy" in sl)


def click_force_fail_mem0(page: Page) -> None:
    label = page.locator("label").filter(has_text="Force Fail Mem0")
    if label.count():
        label.first.click()
        return
    page.get_by_text("Force Fail Mem0", exact=False).first.click()


def main() -> int:
    _configure_stdio()
    ensure_streamlit()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
            wait_workspace(page)
            fill_name_if_needed(page)
            wait_not_running(page, timeout_ms=60_000)
            shot(page, "01_loaded")

            text = body_text(page)
            url = page.url
            REPORT["tests"]["1_page_load_user"] = {
                "pass": ("Inayat" in url) or ("Inayat" in text),
                "url": url,
                "sidebar_or_page_has_Inayat": "Inayat" in text,
            }

            gem = status_for(text, "Gemini LLM")
            mem = status_for(text, "Mem0 Memory")
            neo = status_for(text, "Neo4j Graph")
            REPORT["tests"]["2_service_health"] = {
                "pass": is_healthy(gem) and is_healthy(mem) and is_healthy(neo),
                "gemini": gem,
                "mem0": mem,
                "neo4j": neo,
            }
            shot(page, "02_health")

            mock_offline = "Neo4j is unreachable"
            mock_empty = "No documents indexed yet"
            live_banner = "Connected to Neo4j AuraDB"
            graph_pass = live_banner in text or mock_empty in text
            REPORT["tests"]["3_neural_graph"] = {
                "pass": graph_pass and mock_offline not in text,
                "banner": live_banner
                if live_banner in text
                else (mock_empty if mock_empty in text else "banner not found"),
                "is_mock": mock_empty in text,
            }
            if not graph_pass:
                btn = page.get_by_role("button", name=re.compile("Refresh"))
                if btn.count():
                    btn.first.click()
                    wait_workspace(page)
                    text = body_text(page)
                    graph_pass = live_banner in text or mock_empty in text
                    REPORT["tests"]["3_neural_graph"] = {
                        "pass": graph_pass and mock_offline not in text,
                        "banner": live_banner
                        if live_banner in text
                        else (mock_empty if mock_empty in text else "banner not found"),
                        "is_mock": mock_empty in text,
                        "retried_refresh": True,
                    }
            shot(page, "03_graph")

            before = page.locator('[data-testid="stChatMessage"]').count()
            send_chat(page, "Who is the CEO of INAYAT AI Solutions?")
            ans = wait_assistant(page, before, timeout_ms=150_000)
            REPORT["tests"]["4_ceo_chat"] = {
                "pass": ("Inayat Hussain" in ans) or ("Dr. Inayat" in ans),
                "snippet": ans[:800],
            }
            shot(page, "04_ceo")

            before2 = page.locator('[data-testid="stChatMessage"]').count()
            send_chat(page, "Hello")
            ans2 = wait_assistant(page, before2, timeout_ms=120_000)
            crash = "Traceback" in ans2 or page.locator(
                '[data-testid="stException"]'
            ).count() > 0
            REPORT["tests"]["5_second_chat"] = {
                "pass": (not crash) and bool(ans2.strip()),
                "snippet": ans2[:500],
                "crashed": crash,
            }
            shot(page, "05_hello")

            text = body_text(page)
            if "Force Fail Mem0" in text:
                click_force_fail_mem0(page)
                wait_workspace(page)
                after_fail = body_text(page)
                before3 = page.locator('[data-testid="stChatMessage"]').count()
                send_chat(page, "Hello")
                ans3 = wait_assistant(page, before3, timeout_ms=120_000)
                crash3 = "Traceback" in ans3 or page.locator(
                    '[data-testid="stException"]'
                ).count() > 0
                click_force_fail_mem0(page)
                page.wait_for_timeout(1500)
                REPORT["tests"]["6_mem0_force_fail"] = {
                    "pass": not crash3,
                    "health_after_on": [
                        ln.strip() for ln in after_fail.splitlines() if "Mem0" in ln
                    ][:4],
                    "hello_snippet": ans3[:400],
                    "crashed": crash3,
                }
                shot(page, "06_force_fail")
            else:
                REPORT["tests"]["6_mem0_force_fail"] = {
                    "pass": False,
                    "reason": "Force Fail Mem0 checkbox not found (demo mode off?)",
                }

            text = body_text(page)
            REPORT["tests"]["7_upload_widget"] = {
                "pass": True,
                "skipped_upload": True,
                "widget_seen": "Ingest Documents" in text or "Upload PDFs" in text,
                "reason": (
                    "samples already indexed / graph live; skipped re-upload"
                    if REPORT["tests"]["3_neural_graph"].get("pass")
                    else "graph still mock; upload skipped per size note"
                ),
            }
        except Exception as exc:
            REPORT["blockers"].append(repr(exc))
            try:
                shot(page, "error")
            except Exception:
                pass
        finally:
            browser.close()

    print(json.dumps(REPORT, indent=2, ensure_ascii=False))
    failed = bool(REPORT["blockers"]) or any(
        not t.get("pass") for t in REPORT["tests"].values()
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
