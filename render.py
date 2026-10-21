import re
from datetime import datetime

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


def note_url(p):
    note = p["vault_note"]
    if not note:
        return ""
    if re.match(r"^(https?|obsidian):", note):
        return note
    vault = settings.get("obsidian_vault")
    return f"obsidian://open?vault={vault}&file={note}" if vault else ""


templates.env.filters["ago"] = ago
templates.env.filters["fmtdate"] = lambda ts: ts[5:16].replace("-", ".", 1).replace(" ", ", ") if ts else ""
templates.env.globals["t"] = t
templates.env.globals["site_title"] = lambda: settings.get("site_title")
templates.env.globals["note_url"] = note_url


def slugify(name):
    s = name.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "projekt"
