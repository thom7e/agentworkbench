import re
from datetime import datetime
from urllib.parse import quote

from fastapi.templating import Jinja2Templates

import settings
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
        return "heute"
    if days == 1:
        return "gestern"
    return f"vor {days} Tagen"


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


templates.env.filters["ago"] = ago
templates.env.filters["fmtdate"] = lambda ts: ts[5:16].replace("-", ".", 1).replace(" ", ", ") if ts else ""
templates.env.globals["t"] = t
templates.env.globals["site_title"] = lambda: settings.get("site_title")
templates.env.globals["linked_notes"] = linked_notes


def slugify(name):
    s = name.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "projekt"
