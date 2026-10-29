import re
from contextlib import closing
from datetime import datetime
from urllib.parse import quote

import markdown as _markdown
import nh3
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

import settings
from db import db
from db import BASE
from i18n import t

templates = Jinja2Templates(directory=BASE / "templates")


def ago_days(ts):
    return (datetime.now() - datetime.strptime(ts[:10], "%Y-%m-%d")).days


def ago(ts):
    if not ts:
        return ""
    days = ago_days(ts)
    if days <= 0:
        return t("ago.today")
    if days == 1:
        return t("ago.yesterday")
    return t("ago.days", n=days)


def linked_notes(p):
    out = []
    for line in p["vault_note"].splitlines():
        line = line.strip()
        if not line:
            continue
        label = line.rstrip("/").rsplit("/", 1)[-1].removesuffix(".md")
        if re.match(r"^(https?|obsidian):", line):
            out.append((label if "/" in line else line, line))
        elif settings.get("obsidian_vault"):
            out.append((label, f"obsidian://open?vault={settings.get('obsidian_vault')}&file={quote(line)}"))
    return out


MD_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "li", "strong", "em", "code", "pre", "blockquote",
           "table", "thead", "tbody", "tr", "th", "td", "a", "hr", "br", "del"}


def md(text):
    html = _markdown.markdown(text or "", extensions=["tables", "fenced_code", "sane_lists", "nl2br"])
    html = html.replace("<li>[ ] ", "<li>\u2610 ").replace("<li>[x] ", "<li>\u2611 ").replace("<li>[X] ", "<li>\u2611 ")
    clean = nh3.clean(html, tags=MD_TAGS, attributes={"a": {"href"}}, url_schemes={"http", "https", "mailto", "obsidian"})
    return Markup(clean)


def gb(n):
    return f"{n / 1024 ** 3:.1f} GB".replace(".", ",") if n else "–"


def uptime(sec):
    if not sec:
        return "–"
    days, rest = divmod(int(sec), 86400)
    return t("uptime.days", n=days) if days else t("uptime.hours", n=rest // 3600)


templates.env.filters["gb"] = gb
templates.env.filters["uptime"] = uptime
templates.env.filters["md"] = md
templates.env.filters["ago"] = ago
templates.env.filters["fmtdate"] = lambda ts: ts[5:16].replace("-", ".", 1).replace(" ", ", ") if ts else ""
templates.env.globals["t"] = t
templates.env.globals["_"] = t
templates.env.globals["lang"] = lambda: settings.get("language") if settings.get("language") in ("de", "en") else "de"
templates.env.globals["site_title"] = lambda: settings.get("site_title")
def quick_projects():
    with closing(db()) as con:
        return [(r["slug"], r["name"]) for r in con.execute(
            "SELECT slug, name FROM projects WHERE status='aktiv' ORDER BY live DESC, name COLLATE NOCASE")]


templates.env.globals["linked_notes"] = linked_notes
templates.env.globals["quick_projects"] = quick_projects


def slugify(name):
    s = name.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "projekt"
