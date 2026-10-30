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
import settings
from db import db, now

TIMEOUT = 15


TEXT = {
    "de": {"status": "Status {c}", "missing": "Text fehlt: {t}", "present": "Text vorhanden: {t}", "redirect": "Weiterleitung auf {l}",
           "ok_http": "{u} liefert {c}", "port": "{h}:{p} offen", "unknown": "Unbekannter Typ {k}", "error": "Fehler: {e}",
           "invalid": "Prüfregel ungültig: {e}", "passed": "erfüllt", "open": "offen",
           "log": "Automatisch abgehakt (Prüfregel): {label} – {detail}", "push": "{n} Aufgabe(n) automatisch abgehakt"},
    "en": {"status": "Status {c}", "missing": "Text missing: {t}", "present": "Text present: {t}", "redirect": "Redirects to {l}",
           "ok_http": "{u} returns {c}", "port": "{h}:{p} open", "unknown": "Unknown type {k}", "error": "Error: {e}",
           "invalid": "Invalid check: {e}", "passed": "passed", "open": "open",
           "log": "Ticked off automatically (check): {label} – {detail}", "push": "{n} task(s) ticked off automatically"},
}


def tx(key, **kw):
    return (TEXT.get(settings.get("language")) or TEXT["de"])[key].format(**kw)


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
            return False, tx("status", c=status)
        if spec.get("contains") and spec["contains"] not in body:
            return False, tx("missing", t=spec["contains"][:40])
        if spec.get("not_contains") and spec["not_contains"] in body:
            return False, tx("present", t=spec["not_contains"][:40])
        if spec.get("location_contains") and spec["location_contains"] not in (headers.get("Location") or ""):
            return False, tx("redirect", l=headers.get("Location"))
        return True, tx("ok_http", u=spec["url"], c=status)
    if kind == "dns":
        ips = socket.gethostbyname_ex(spec["host"])[2]
        return spec["ip"] in ips, f"{spec['host']} -> {', '.join(ips)}"
    if kind == "port":
        with socket.create_connection((spec["host"], int(spec["port"])), timeout=TIMEOUT):
            return True, tx("port", h=spec["host"], p=spec["port"])
    return False, tx("unknown", k=kind)


def run_check(raw):
    specs = json.loads(raw)
    specs = specs if isinstance(specs, list) else [specs]
    details = []
    for spec in specs:
        try:
            ok, detail = check_one(spec)
        except Exception as e:
            ok, detail = False, tx("error", e=e)
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
            ok, detail = False, tx("invalid", e=e)
        label = r["short"] or r["text"][:80]
        print(("OK   " if ok else "offen"), f"[{r['name']}] {label} – {detail}")
        if dry:
            continue
        con.execute("UPDATE todos SET check_note=? WHERE id=?", (f"{tx('passed' if ok else 'open')}: {detail} ({now()})", r["id"]))
        if ok:
            con.execute("UPDATE todos SET done=1, done_at=? WHERE id=?", (now(), r["id"]))
            con.execute("INSERT INTO activity(project,text,ts) VALUES(?,?,?)",
                        (r["project"], tx("log", label=label, detail=detail), now()))
            ticked.append((r["name"], label))
        con.commit()
    return ticked


def notify(ticked):
    push.send(tx("push", n=len(ticked)), ", ".join(label for _, label in ticked), "/")


if __name__ == "__main__":
    with closing(db()) as con:
        done = run_all(con, dry="--dry" in sys.argv)
    if done:
        notify(done)
