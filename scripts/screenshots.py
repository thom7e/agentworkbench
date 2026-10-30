"""Create the README screenshots from the demo data.

    pip install playwright
    AGENTWORKBENCH_DB=./demo.db python scripts/demo_seed.py
    AGENTWORKBENCH_DB=./demo.db uvicorn app:app --port 8777 &
    python scripts/screenshots.py http://127.0.0.1:8777

Uses the Chrome that is installed on the machine (no browser download).
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8777"
OUT = Path(__file__).resolve().parent.parent / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)
PASSWORD = "demo-password-123"
PHONE = dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)


def login(page):
    page.goto(BASE + "/login")
    page.fill("input[name=password]", PASSWORD)
    page.click("button.go")
    page.wait_for_url(BASE + "/")
    page.wait_for_timeout(600)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    for scheme in ("light", "dark"):
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, color_scheme=scheme)
        page = ctx.new_page()
        login(page)
        page.screenshot(path=str(OUT / f"dashboard-{scheme}.png"))
        if scheme == "light":
            page.goto(BASE + "/p/dental-booking")
            page.wait_for_timeout(500)
            page.screenshot(path=str(OUT / "project.png"))
            page.goto(BASE + "/briefing")
            page.wait_for_timeout(500)
            page.screenshot(path=str(OUT / "briefing.png"))
            page.goto(BASE + "/admin/settings")
            page.set_viewport_size({"width": 1440, "height": 1100})
            page.screenshot(path=str(OUT / "admin.png"))
        ctx.close()
    ctx = browser.new_context(color_scheme="light", **PHONE)
    page = ctx.new_page()
    login(page)
    page.screenshot(path=str(OUT / "mobile.png"))
    page.click(".tabbar a[data-tab-link=projects]")
    page.wait_for_timeout(400)
    page.screenshot(path=str(OUT / "mobile-projects.png"))
    ctx.close()
    browser.close()
print("screenshots written to", OUT)
