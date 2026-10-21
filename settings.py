import json
from contextlib import closing

from db import db

DEFAULTS = {
    "site_title": "AgentWorkbench",
    "language": "de",
    "github_owner": "",
    "github_token": "",
    "dormant_days": "90",
    "default_sort": "aktuell",
    "areas": json.dumps(["Allgemein"]),
    "obsidian_vault": "",
    "proxmox_url": "",
    "proxmox_token_id": "",
    "proxmox_token_secret": "",
    "proxmox_verify_tls": "0",
}


def get(key):
    with closing(db()) as con:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else DEFAULTS.get(key, "")


def put(key, value):
    with closing(db()) as con:
        con.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        con.commit()


def areas():
    try:
        names = [a for a in json.loads(get("areas")) if a]
    except ValueError:
        names = []
    return names or ["Allgemein"]
