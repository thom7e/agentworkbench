import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = os.environ.get("AGENTWORKBENCH_DB", str(BASE / "dashboard.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'aktiv',
    deploy TEXT DEFAULT '',
    stack TEXT DEFAULT '',
    summary TEXT DEFAULT '',
    vault_note TEXT DEFAULT '',
    repo TEXT DEFAULT '',
    wiki TEXT DEFAULT '',
    sort INTEGER DEFAULT 100
);
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL REFERENCES projects(slug) ON DELETE CASCADE ON UPDATE CASCADE,
    text TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'todo',
    prio INTEGER NOT NULL DEFAULT 2,
    done INTEGER NOT NULL DEFAULT 0,
    created TEXT NOT NULL,
    done_at TEXT
);
CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL REFERENCES projects(slug) ON DELETE CASCADE ON UPDATE CASCADE,
    text TEXT NOT NULL,
    ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL REFERENCES projects(slug) ON DELETE CASCADE ON UPDATE CASCADE,
    text TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT 'user',
    pinned INTEGER NOT NULL DEFAULT 0,
    created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS docs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL REFERENCES projects(slug) ON DELETE CASCADE ON UPDATE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    created TEXT NOT NULL,
    updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created TEXT NOT NULL,
    last_used TEXT
);
"""

# Spalten, die nach dem ersten Release dazugekommen sind
MIGRATIONS = (
    ("todos", "source TEXT NOT NULL DEFAULT 'user'"),
    ("todos", "seen INTEGER NOT NULL DEFAULT 1"),
    ("todos", "short TEXT NOT NULL DEFAULT ''"),
    ("projects", "area TEXT NOT NULL DEFAULT ''"),
    ("projects", "vmid INTEGER NOT NULL DEFAULT 0"),
)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init():
    with closing(db()) as con:
        con.executescript(SCHEMA)
        for table, col in MIGRATIONS:
            try:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass
        con.commit()
