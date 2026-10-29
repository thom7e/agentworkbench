"""Daily morning digest: builds a plain-text summary from the dashboard DB and sends it via Telegram.

Usage: python digest.py [--print]   (--print only prints, nothing is sent)
Telegram credentials (TG_BOT_TOKEN, TG_CHAT_ID) come from the environment or the file in DIGEST_ENV.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from contextlib import closing
from datetime import datetime, timedelta

from db import db

DAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
STALE_DAYS = 14
LIMIT = 8


def clip(text, n=110):
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


def section(title, lines, total=None):
    if not lines:
        return []
    more = (total or len(lines)) - len(lines)
    return [title, *lines, *([f"  … und {more} weitere"] if more > 0 else []), ""]


def build_digest(con, today=None):
    today = today or datetime.now()
    day = today.strftime("%Y-%m-%d")
    yday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    stale = (today - timedelta(days=STALE_DAYS)).strftime("%Y-%m-%d")
    names = {r["slug"]: r["name"] for r in con.execute("SELECT slug, name FROM projects")}

    def n(slug):
        return names.get(slug, slug)

    p1 = con.execute("SELECT project, text FROM todos WHERE done=0 AND kind='todo' AND prio=1 ORDER BY created").fetchall()
    open_p2 = con.execute("SELECT COUNT(*) FROM todos WHERE done=0 AND kind='todo' AND prio=2").fetchone()[0]
    done_y = con.execute("SELECT project, text FROM todos WHERE done=1 AND done_at>=? AND done_at<? ORDER BY done_at",
                         (yday, day)).fetchall()
    log_y = con.execute("SELECT project, text FROM activity WHERE ts>=? AND ts<? ORDER BY ts", (yday, day)).fetchall()
    ideas = con.execute("SELECT project, text FROM todos WHERE kind='idee' AND done=0 AND created>=? ORDER BY created",
                        (yday,)).fetchall()
    quiet = con.execute(
        "SELECT p.name, COUNT(t.id) c FROM projects p JOIN todos t ON t.project=p.slug AND t.done=0 AND t.kind='todo' "
        "WHERE p.status='aktiv' AND COALESCE((SELECT MAX(ts) FROM activity a WHERE a.project=p.slug),'')<? "
        "GROUP BY p.slug ORDER BY c DESC", (stale,)).fetchall()

    out = [f"Guten Morgen! {DAYS[today.weekday()]}, {today.strftime('%d.%m.')}", ""]
    out += section(f"Dringend (P1): {len(p1)}", [f"• {n(r['project'])}: {clip(r['text'])}" for r in p1[:LIMIT]], len(p1))
    out += [f"Offene Aufgaben P2: {open_p2}", ""]
    out += section(f"Gestern erledigt: {len(done_y)}", [f"✓ {n(r['project'])}: {clip(r['text'], 80)}" for r in done_y[:LIMIT]], len(done_y))
    out += section("Verlauf gestern", [f"• {n(r['project'])}: {clip(r['text'], 80)}" for r in log_y[:LIMIT]], len(log_y))
    out += section(f"Neue Ideen: {len(ideas)}", [f"• {n(r['project'])}: {clip(r['text'], 80)}" for r in ideas[:5]], len(ideas))
    out += section(f"Ruhend (> {STALE_DAYS} Tage ohne Eintrag, offene Todos)", [f"• {r['name']} ({r['c']})" for r in quiet[:5]], len(quiet))
    return "\n".join(out).strip()


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
    data = urllib.parse.urlencode({"chat_id": chat, "text": text[:4000]}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=20) as r:
        if not json.load(r)["ok"]:
            raise RuntimeError("Telegram send failed")


if __name__ == "__main__":
    with closing(db()) as con:
        text = build_digest(con)
    print(text) if "--print" in sys.argv else send(text)
