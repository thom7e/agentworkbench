import json
import time
from contextlib import closing

import db as database

DEFAULTS = {
    "site_title": "AgentWorkbench",
    "language": "de",
    "github_owner": "",
    "github_token": "",
    "dormant_days": "90",
    "default_sort": "aktuell",
    "areas": json.dumps(["Allgemein"]),
    "proxmox_url": "",
    "proxmox_token_id": "",
    "proxmox_token_secret": "",
    "proxmox_verify_tls": "0",
    "owner_name": "",
    "push_contact": "mailto:admin@example.com",
}


TTL = 5
_cache = {}


def get(key):
    ck = (database.DB_PATH, key)
    hit = _cache.get(ck)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    with closing(database.db()) as con:
        row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    value = row["value"] if row else DEFAULTS.get(key, "")
    _cache[ck] = (time.time(), value)
    return value


def put(key, value):
    with closing(database.db()) as con:
        con.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        con.commit()
    _cache[(database.DB_PATH, key)] = (time.time(), value)


def areas():
    try:
        names = [a for a in json.loads(get("areas")) if a]
    except ValueError:
        names = []
    return names or ["Allgemein"]
