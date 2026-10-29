from contextlib import closing
from datetime import datetime

import db
import digest

TODAY = datetime(2026, 10, 29, 7, 0)


def seed(con):
    con.execute("INSERT INTO projects(slug,name,repo) VALUES('a','Alpha','o/alpha')")
    con.execute("INSERT INTO projects(slug,name,repo,live) VALUES('b','Beta','o/beta',1)")
    con.execute("INSERT INTO projects(slug,name,repo,live) VALUES('c','Gamma','o/gamma',1)")
    con.execute("INSERT INTO projects(slug,name,status,repo) VALUES('z','Zeta','archiv','o/zeta')")
    con.execute("INSERT INTO todos(project,text,prio,created) VALUES('a','Normales',2,'2026-10-20 10:00')")
    con.execute("INSERT INTO todos(project,text,short,prio,created) VALUES('b','**Lang** `x`: Details',"
                "'Dringendes erledigen',1,'2026-10-20 10:00')")
    con.execute("INSERT INTO todos(project,text,prio,created) VALUES('b','Zweites',2,'2026-10-20 10:00')")
    con.execute("INSERT INTO todos(project,text,prio,created) VALUES('c','Schlafendes Projekt',1,'2026-10-20 10:00')")
    con.execute("INSERT INTO todos(project,text,prio,created) VALUES('z','Altlast',1,'2026-10-20 10:00')")
    con.execute("INSERT INTO todos(project,text,prio,done,created) VALUES('a','Fertig',1,1,'2026-10-20 10:00')")
    con.commit()


def test_digest_all_active_projects_p1_first(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "digest.db"))
    db.init()
    with closing(db.db()) as con:
        seed(con)
        text = digest.build_digest(con, TODAY, prs=[])
    assert "Guten Morgen, Thomas" in text and "Donnerstag, 29.10." in text
    assert "<b>Dringend</b>" in text and "<b>Beta</b><br>Dringendes erledigen; Zweites." in text
    assert text.index("Beta") < text.index("Alpha") and "<b>Sonst offen</b><br>Alpha (1)" in text
    assert "<b>Gamma</b>" in text and "Zeta" not in text and "Fertig" not in text


def test_open_prs_are_listed(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "digest.db"))
    db.init()
    with closing(db.db()) as con:
        seed(con)
        text = digest.build_digest(con, TODAY, prs=[{"repo": "o/gamma", "title": "x"}])
    assert "<b>Pull Requests</b>: gamma" in text


def test_plain_strips_markup_and_paths():
    t = digest.plain("**Prod-Deploy** (staging → main): `.env` vorher aus dem Git-Index, `update_db.py` und mehr Text hier")
    assert "`" not in t and "*" not in t and len(t) <= 90


def test_stale_todos_are_called_out(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "digest.db"))
    db.init()
    with closing(db.db()) as con:
        con.execute("INSERT INTO projects(slug,name,live) VALUES('a','Alpha',1)")
        con.execute("INSERT INTO todos(project,text,prio,created) VALUES('a','Alt',2,'2026-08-01 10:00')")
        con.execute("INSERT INTO todos(project,text,prio,created) VALUES('a','Alt2',1,'2026-09-01 10:00')")
        con.execute("INSERT INTO todos(project,text,prio,created) VALUES('a','Neu',2,'2026-10-28 10:00')")
        con.commit()
        text = digest.build_digest(con, TODAY, prs=[])
    assert "<b>Länger offen</b><br>2 Aufgaben seit über 30 Tagen offen: Alpha (2)" in text
