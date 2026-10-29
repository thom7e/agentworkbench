"""Daily machine checks for todos: a todo with a check spec is ticked off automatically once the check passes.

A spec is a JSON object (or a list of objects, all must pass):
  {"type": "http", "url": "https://example.com/x", "status": 200, "contains": "text", "not_contains": "text",
   "location_contains": "text"}   (location_contains also stops redirects from being followed)
  {"type": "dns", "host": "example.com", "ip": "1.2.3.4"}
  {"type": "port", "host": "example.com", "port": 443}

Usage: python checks.py [--dry]   (--dry reports results without ticking anything off)
"""
import json
import socket
import sys
import urllib.error
import urllib.request
from contextlib import closing

import push
from db import db, now

TIMEOUT = 15


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fetch(url, follow):
    opener = urllib.request.build_opener(*([] if follow else [_NoRedirect]))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 agentworkbench-check"})
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.status, r.headers, r.read(2_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read(200_000).decode("utf-8", "replace")


def check_one(spec):
    kind = spec.get("type")
    if kind == "http":
        status, headers, body = fetch(spec["url"], follow="location_contains" not in spec)
        if status != spec.get("status", 200):
            return False, f"Status {status}"
        if spec.get("contains") and spec["contains"] not in body:
            return False, f"Text fehlt: {spec['contains'][:40]}"
        if spec.get("not_contains") and spec["not_contains"] in body:
            return False, f"Text vorhanden: {spec['not_contains'][:40]}"
        if spec.get("location_contains") and spec["location_contains"] not in (headers.get("Location") or ""):
            return False, f"Weiterleitung auf {headers.get('Location')}"
        return True, f"{spec['url']} liefert {status}"
    if kind == "dns":
        ips = socket.gethostbyname_ex(spec["host"])[2]
        return spec["ip"] in ips, f"{spec['host']} -> {', '.join(ips)}"
    if kind == "port":
        with socket.create_connection((spec["host"], int(spec["port"])), timeout=TIMEOUT):
            return True, f"{spec['host']}:{spec['port']} offen"
    return False, f"Unbekannter Typ {kind}"


def run_check(raw):
    specs = json.loads(raw)
    specs = specs if isinstance(specs, list) else [specs]
    details = []
    for spec in specs:
        try:
            ok, detail = check_one(spec)
        except Exception as e:
            ok, detail = False, f"Fehler: {e}"
        details.append(detail)
        if not ok:
            return False, "; ".join(details)
    return True, "; ".join(details)


def run_all(con, dry=False):
    ticked = []
    rows = con.execute("SELECT t.id, t.project, t.text, t.short, p.name FROM todos t JOIN projects p ON p.slug=t.project "
                       "WHERE t.done=0 AND t.check_spec!=''").fetchall()
    for r in rows:
        raw = con.execute("SELECT check_spec FROM todos WHERE id=?", (r["id"],)).fetchone()[0]
        try:
            ok, detail = run_check(raw)
        except Exception as e:
            ok, detail = False, f"Prüfregel ungültig: {e}"
        label = r["short"] or r["text"][:80]
        print(("OK   " if ok else "offen"), f"[{r['name']}] {label} – {detail}")
        if dry:
            continue
        con.execute("UPDATE todos SET check_note=? WHERE id=?", (f"{'erfüllt' if ok else 'offen'}: {detail} ({now()})", r["id"]))
        if ok:
            con.execute("UPDATE todos SET done=1, done_at=? WHERE id=?", (now(), r["id"]))
            con.execute("INSERT INTO activity(project,text,ts) VALUES(?,?,?)",
                        (r["project"], f"Automatisch abgehakt (Prüfregel): {label} – {detail}", now()))
            ticked.append((r["name"], label))
        con.commit()
    return ticked


def notify(ticked):
    push.send(f"{len(ticked)} Aufgabe(n) automatisch abgehakt", ", ".join(label for _, label in ticked), "/")


if __name__ == "__main__":
    with closing(db()) as con:
        done = run_all(con, dry="--dry" in sys.argv)
    if done:
        notify(done)
