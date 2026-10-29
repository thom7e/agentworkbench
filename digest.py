"""Daily morning digest: builds a plain-text summary from the dashboard DB and sends it via Telegram.

Usage: python digest.py [--print]   (--print only prints, nothing is sent)
Telegram credentials (TG_BOT_TOKEN, TG_CHAT_ID) come from the environment or the file in DIGEST_ENV.
"""
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from contextlib import closing
from datetime import datetime, timedelta

import github
from db import db

DAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
HIDDEN = ("archiv", "archived", "pause")
MAX_LEN = 3900
ACTIVE_DAYS = 14
MAX_NORMAL = 10


def plain(text, n=90):
    """Fallback for todos without a short title: strip markup, paths and code, keep the first sentence."""
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"[*_#]", "", text)
    text = re.sub(r"\s+", " ", text).strip(" -–—:;,.")
    if len(text) > n:
        text = re.split(r"(?<=[.!?])\s|\s[—–]\s|:\s", text, maxsplit=1)[0]
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def phrase(rows, limit, tail="weitere"):
    items = [r["short"] or plain(r["text"]) for r in rows]
    text = "; ".join(items[:limit])
    return text + (f" (+{len(items) - limit} {tail})" if len(items) > limit else "")


def active_slugs(con, today, pushed, prs):
    """Projects with a push or a log entry in the last ACTIVE_DAYS days, or with an open pull request."""
    since = (today - timedelta(days=ACTIVE_DAYS)).strftime("%Y-%m-%d")
    out = {r["project"] for r in con.execute("SELECT DISTINCT project FROM activity WHERE ts>=?", (since,))}
    for p in con.execute("SELECT slug, repo FROM projects WHERE repo!=''"):
        repo = p["repo"].lower()
        if pushed.get(repo, "")[:10] >= since or any(pr["repo"].lower() == repo for pr in prs):
            out.add(p["slug"])
    return out


def build_digest(con, today=None, pushed=None, prs=None, url=""):
    today = today or datetime.now()
    pushed = github.pushed_map() if pushed is None else pushed
    prs = github.open_prs() if prs is None else prs
    live = active_slugs(con, today, pushed, prs)
    marks = ",".join("?" * len(HIDDEN))
    rows = con.execute(
        f"SELECT p.slug, p.name, t.prio, t.text, t.short FROM todos t JOIN projects p ON p.slug=t.project "
        f"WHERE t.done=0 AND t.kind='todo' AND t.prio<=2 AND p.status NOT IN ({marks}) ORDER BY t.prio, t.id", HIDDEN).fetchall()
    projects = {}
    for r in rows:
        if r["slug"] in live:
            projects.setdefault(r["name"], []).append(r)
    urgent = [k for k, v in projects.items() if any(r["prio"] == 1 for r in v)]
    normal = [k for k in projects if k not in urgent]
    h = html.escape
    out = [f"Guten Morgen, Thomas. Dein Briefing für {DAYS[today.weekday()]}, {today.strftime('%d.%m.')}"]
    if urgent:
        out += ["", f"<b>Dringend</b> – {len(urgent)} {'Projekt' if len(urgent) == 1 else 'Projekte'} zuerst:"]
        for k in sorted(urgent, key=str.lower):
            p1 = [r for r in projects[k] if r["prio"] == 1]
            more = len(projects[k]) - len(p1)
            line = f"<b>{h(k)}</b>\n{h(phrase(p1, 3, "dringende"))}."
            if more:
                line += f" Dazu {more} weitere offen."
            out += ["", line]
    if normal:
        top = sorted(normal, key=lambda k: (-len(projects[k]), k.lower()))
        names = ", ".join(f"{k} ({len(projects[k])})" for k in top[:MAX_NORMAL])
        out += ["", f"<b>Sonst offen</b>\n{h(names)}" + (f" und {len(top) - MAX_NORMAL} weitere" if len(top) > MAX_NORMAL else "")]
    if not projects:
        out += ["", "Nichts Dringendes in den aktiven Projekten."]
    if prs:
        out += ["", f"<b>Pull Requests</b>: {h(', '.join(sorted({pr['repo'].split('/')[-1] for pr in prs})))}"]
    if url:
        out += ["", f'<a href="{h(url)}">Mehr im Dashboard</a>']
    return "\n".join(out)


def chunks(text):
    parts, cur = [], ""
    for block in text.split("\n\n"):
        if cur and len(cur) + len(block) + 2 > MAX_LEN:
            parts.append(cur)
            cur = ""
        cur = f"{cur}\n\n{block}" if cur else block
    return [*parts, cur]


def load_env():
    path = os.environ.get("DIGEST_ENV", "/etc/dashboard-digest.env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)


def send(text):
    load_env()
    token, chat = os.environ["TG_BOT_TOKEN"], os.environ["TG_CHAT_ID"]
    for part in chunks(text):
        data = urllib.parse.urlencode({"chat_id": chat, "text": part, "parse_mode": "HTML",
                                       "disable_web_page_preview": "true"}).encode()
        with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=20) as r:
            if not json.load(r)["ok"]:
                raise RuntimeError("Telegram send failed")


if __name__ == "__main__":
    with closing(db()) as con:
        load_env()
        text = build_digest(con, url=os.environ.get("DASHBOARD_URL", ""))
    print(text) if "--print" in sys.argv else send(text)
