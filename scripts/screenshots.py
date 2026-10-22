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


def login(page):
    page.goto(BASE + "/login")
    page.fill("input[name=password]", PASSWORD)
    page.click("button.go")
    page.wait_for_url(BASE + "/")


with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    for scheme in ("dark", "light"):
        ctx = browser.new_context(viewport={"width": 1280, "height": 1500}, color_scheme=scheme)
        page = ctx.new_page()
        login(page)
        page.add_style_tag(content="*{caret-color:transparent}")
        page.screenshot(path=str(OUT / f"dashboard-{scheme}.png"))
        if scheme == "dark":
            page.goto(BASE + "/p/nas-backup")
            page.screenshot(path=str(OUT / "project.png"))
            page.goto(BASE + "/admin/settings")
            page.set_viewport_size({"width": 1280, "height": 1100})
            page.screenshot(path=str(OUT / "admin.png"))
        ctx.close()
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, color_scheme="dark",
                              is_mobile=True, has_touch=True)
    page = ctx.new_page()
    login(page)
    page.screenshot(path=str(OUT / "mobile.png"))
    ctx.close()
    browser.close()
print("screenshots written to", OUT)
