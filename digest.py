"""Daily morning digest: builds a plain-text summary from the dashboard DB and sends it via Telegram.

Usage: python digest.py [--print]   (--print only prints, nothing is sent)
Telegram credentials (TG_BOT_TOKEN, TG_CHAT_ID) come from the environment or the file in DIGEST_ENV.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from contextlib import closing
from datetime import datetime

from db import db

DAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
HIDDEN = ("archiv", "archived", "pause")
MAX_LEN = 3900


def plain(text, n=90):
    """Fallback for todos without a short title: strip markup, paths and code, keep the first sentence."""
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"[*_#]", "", text)
    text = re.sub(r"\s+", " ", text).strip(" -–—:;,.")
    if len(text) > n:
        text = re.split(r"(?<=[.!?])\s|\s[—–]\s|:\s", text, maxsplit=1)[0]
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def build_digest(con, today=None):
    today = today or datetime.now()
    marks = ",".join("?" * len(HIDDEN))
    rows = con.execute(
        f"SELECT p.name, t.prio, t.text, t.short FROM todos t JOIN projects p ON p.slug=t.project "
        f"WHERE t.done=0 AND t.kind='todo' AND t.prio<=2 AND p.status NOT IN ({marks})", HIDDEN).fetchall()
    projects = {}
    for r in rows:
        projects.setdefault(r["name"], []).append(r)
    order = sorted(projects, key=lambda k: (-sum(r["prio"] == 1 for r in projects[k]), k.lower()))
    p1 = sum(r["prio"] == 1 for r in rows)
    out = [f"Guten Morgen! {DAYS[today.weekday()]}, {today.strftime('%d.%m.')}",
           f"{p1} dringend (!), {len(rows) - p1} normal", ""]
    for name in order:
        out.append(name)
        for r in sorted(projects[name], key=lambda r: r["prio"]):
            out.append(f"{'!' if r['prio'] == 1 else '·'} {r['short'] or plain(r['text'])}")
        out.append("")
    return "\n".join(out).strip()


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
        data = urllib.parse.urlencode({"chat_id": chat, "text": part}).encode()
        with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=20) as r:
            if not json.load(r)["ok"]:
                raise RuntimeError("Telegram send failed")


if __name__ == "__main__":
    with closing(db()) as con:
        text = build_digest(con)
    print(text) if "--print" in sys.argv else send(text)
