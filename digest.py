"""Daily morning briefing: builds a short summary from the dashboard DB and sends it as a web push notification.

Usage: python digest.py [--print]   (--print only prints, nothing is sent)
The notification opens /briefing, which renders the same text and lets you choose which projects are shown in detail.
The text follows the interface language from the settings (de or en).
"""
import html
import re
import sys
from contextlib import closing
from datetime import datetime, timedelta

import github
import push
import settings
from db import db

HIDDEN = ("archiv", "archived", "pause")
MAX_NORMAL = 20
STALE_DAYS = 30

TEXT = {
    "de": {
        "days": ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"),
        "date": "%d.%m.",
        "hello": "Guten Morgen{name}. Dein Briefing für {day}, {date}",
        "urgent": "<b>Dringend</b> – live oder beim Kunden ({n}):",
        "more": "weitere",
        "rest": "<b>Sonst offen</b>",
        "and_more": " und {n} weitere",
        "stale": "<b>Länger offen</b><br>{n} Aufgaben seit über {days} Tagen offen: {names}",
        "none": "Nichts Dringendes in den aktiven Projekten.",
        "prs": "<b>Pull Requests</b>",
        "push": "Morgen-Briefing",
    },
    "en": {
        "days": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"),
        "date": "%m/%d",
        "hello": "Good morning{name}. Your briefing for {day}, {date}",
        "urgent": "<b>Urgent</b> – live or at the customer ({n}):",
        "more": "more",
        "rest": "<b>Everything else open</b>",
        "and_more": " and {n} more",
        "stale": "<b>Open for a long time</b><br>{n} tasks open for over {days} days: {names}",
        "none": "Nothing urgent in the active projects.",
        "prs": "<b>Pull requests</b>",
        "push": "Morning briefing",
    },
}


def tx():
    return TEXT.get(settings.get("language")) or TEXT["de"]


def plain(text, n=90):
    """Fallback for todos without a short title: strip markup, paths and code, keep the first sentence."""
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"[*_#]", "", text)
    text = re.sub(r"\s+", " ", text).strip(" -–—:;,.")
    if len(text) > n:
        text = re.split(r"(?<=[.!?])\s|\s[—–]\s|:\s", text, maxsplit=1)[0]
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def phrase(rows, limit, tail=None):
    tail = tail or tx()["more"]
    items = [r["short"] or plain(r["text"]) for r in rows]
    text = "; ".join(items[:limit])
    return text + (f" (+{len(items) - limit} {tail})" if len(items) > limit else "")


def build_digest(con, today=None, prs=None):
    today = today or datetime.now()
    prs = github.open_prs() if prs is None else prs
    T = tx()
    marks = ",".join("?" * len(HIDDEN))
    rows = con.execute(
        f"SELECT p.name, p.live, t.prio, t.text, t.short, t.created FROM todos t JOIN projects p ON p.slug=t.project "
        f"WHERE t.done=0 AND t.kind='todo' AND t.prio<=2 AND p.status NOT IN ({marks}) ORDER BY t.prio, t.id", HIDDEN).fetchall()
    projects = {}
    for r in rows:
        projects.setdefault(r["name"], []).append(r)
    urgent = [k for k, v in projects.items() if v[0]["live"]]
    normal = [k for k in projects if k not in urgent]
    h = html.escape
    owner = settings.get("owner_name").strip()
    out = [T["hello"].format(name=", " + owner if owner else "", day=T["days"][today.weekday()], date=today.strftime(T["date"]))]
    if urgent:
        out += ["", T["urgent"].format(n=len(urgent))]
        for k in sorted(urgent, key=lambda k: (-sum(r["prio"] == 1 for r in projects[k]), k.lower())):
            out += ["", f"<b>{h(k)}</b><br>{h(phrase(projects[k], 3))}."]
    if normal:
        top = sorted(normal, key=lambda k: (-len(projects[k]), k.lower()))
        names = ", ".join(f"{k} ({len(projects[k])})" for k in top[:MAX_NORMAL])
        out += ["", f"{T['rest']}<br>{h(names)}" + (T["and_more"].format(n=len(top) - MAX_NORMAL) if len(top) > MAX_NORMAL else "")]
    cutoff = (today - timedelta(days=STALE_DAYS)).strftime("%Y-%m-%d")
    stale = {}
    for r in rows:
        if r["created"][:10] < cutoff:
            stale[r["name"]] = stale.get(r["name"], 0) + 1
    if stale:
        names = ", ".join(f"{k} ({n})" for k, n in sorted(stale.items(), key=lambda kv: (-kv[1], kv[0].lower()))[:5])
        out += ["", T["stale"].format(n=sum(stale.values()), days=STALE_DAYS, names=h(names))]
    if not projects:
        out += ["", T["none"]]
    if prs:
        out += ["", f"{T['prs']}: {h(', '.join(sorted({pr['repo'].split('/')[-1] for pr in prs})))}"]
    return "\n".join(out)


def summary_counts(con):
    """(projects that are live and have open P1/P2 todos, other projects with open P1/P2 todos)."""
    marks = ",".join("?" * len(HIDDEN))
    rows = con.execute(
        f"SELECT p.slug, p.live FROM todos t JOIN projects p ON p.slug=t.project "
        f"WHERE t.done=0 AND t.kind='todo' AND t.prio<=2 AND p.status NOT IN ({marks}) GROUP BY p.slug", HIDDEN).fetchall()
    urgent = sum(1 for r in rows if r["live"])
    return urgent, len(rows) - urgent


def briefing_projects(con):
    """Projects offered in the briefing settings: live ones plus everything with open todos."""
    marks = ",".join("?" * len(HIDDEN))
    return con.execute(
        f"SELECT slug, name, live FROM projects WHERE status NOT IN ({marks}) AND (live=1 OR EXISTS "
        f"(SELECT 1 FROM todos t WHERE t.project=projects.slug AND t.done=0 AND t.kind='todo')) "
        f"ORDER BY live DESC, name COLLATE NOCASE", HIDDEN).fetchall()


def push_briefing(text):
    lines = [re.sub(r"<[^>]+>", "", line) for line in text.replace("<br>", " – ").splitlines() if line.strip()]
    return push.send(tx()["push"], " ".join(lines[1:3]), "/briefing")


if __name__ == "__main__":
    with closing(db()) as con:
        text = build_digest(con)
    print(text) if "--print" in sys.argv else push_briefing(text)
