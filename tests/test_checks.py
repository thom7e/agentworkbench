import json
from contextlib import closing

import checks
import db


def test_http_spec_judging(monkeypatch):
    monkeypatch.setattr(checks, "fetch", lambda url, follow: (200, {}, "<urlset> ok"))
    assert checks.run_check(json.dumps({"type": "http", "url": "u", "contains": "<urlset"}))[0]
    assert not checks.run_check(json.dumps({"type": "http", "url": "u", "contains": "<sitemapindex"}))[0]
    assert not checks.run_check(json.dumps({"type": "http", "url": "u", "not_contains": "ok"}))[0]
    assert not checks.run_check(json.dumps({"type": "http", "url": "u", "status": 301}))[0]
    monkeypatch.setattr(checks, "fetch", lambda url, follow: (301, {"Location": "https://x/y"}, ""))
    assert checks.run_check(json.dumps({"type": "http", "url": "u", "status": 301, "location_contains": "x/y"}))[0]


def test_list_needs_all_and_bad_spec_is_open(monkeypatch):
    monkeypatch.setattr(checks, "fetch", lambda url, follow: (404 if "bad" in url else 200, {}, ""))
    both = [{"type": "http", "url": "good"}, {"type": "http", "url": "bad"}]
    assert not checks.run_check(json.dumps(both))[0]
    assert not checks.run_check(json.dumps({"type": "nope"}))[0]


def test_run_all_ticks_passing_todo_and_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "c.db"))
    monkeypatch.setattr(checks, "fetch", lambda url, follow: (200, {}, ""))
    db.init()
    with closing(db.db()) as con:
        con.execute("INSERT INTO projects(slug,name) VALUES('a','Alpha')")
        spec = json.dumps({"type": "http", "url": "https://ok"})
        con.execute("INSERT INTO todos(project,text,created,check_spec) VALUES('a','Seite online',?,?)", ("2026-10-29 07:00", spec))
        con.execute("INSERT INTO todos(project,text,created,check_spec) VALUES('a','Nie',?,?)",
                    ("2026-10-29 07:00", json.dumps({"type": "http", "url": "https://x", "status": 500})))
        con.commit()
        ticked = checks.run_all(con)
        assert ticked == [("Alpha", "Seite online")]
        assert con.execute("SELECT done FROM todos WHERE text='Nie'").fetchone()[0] == 0
        assert "offen" in con.execute("SELECT check_note FROM todos WHERE text='Nie'").fetchone()[0]
        assert "Automatisch abgehakt" in con.execute("SELECT text FROM activity").fetchone()[0]
