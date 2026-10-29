from contextlib import closing
from datetime import datetime

import db
import digest

TODAY = datetime(2026, 10, 29, 7, 0)


def seed(con):
    con.execute("INSERT INTO projects(slug,name,repo) VALUES('a','Alpha','o/alpha')")
    con.execute("INSERT INTO projects(slug,name,repo) VALUES('b','Beta','o/beta')")
    con.execute("INSERT INTO projects(slug,name,repo) VALUES('c','Gamma','o/gamma')")
    con.execute("INSERT INTO projects(slug,name,status,repo) VALUES('z','Zeta','archiv','o/zeta')")
    con.execute("INSERT INTO todos(project,text,prio,created) VALUES('a','Normales',2,'2026-10-20 10:00')")
    con.execute("INSERT INTO todos(project,text,short,prio,created) VALUES('b','**Lang** `x`: Details',"
                "'Dringendes erledigen',1,'2026-10-20 10:00')")
    con.execute("INSERT INTO todos(project,text,prio,created) VALUES('b','Zweites',2,'2026-10-20 10:00')")
    con.execute("INSERT INTO todos(project,text,prio,created) VALUES('c','Schlafendes Projekt',1,'2026-10-20 10:00')")
    con.execute("INSERT INTO todos(project,text,prio,created) VALUES('z','Altlast',1,'2026-10-20 10:00')")
    con.execute("INSERT INTO todos(project,text,prio,done,created) VALUES('a','Fertig',1,1,'2026-10-20 10:00')")
    con.commit()


def test_digest_only_active_projects_p1_first(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "digest.db"))
    db.init()
    with closing(db.db()) as con:
        seed(con)
        pushed = {"o/alpha": "2026-10-27T10:00:00Z", "o/beta": "2026-10-28T10:00:00Z", "o/zeta": "2026-10-28T10:00:00Z"}
        text = digest.build_digest(con, TODAY, pushed=pushed, prs=[], url="http://dash")
    assert "Guten Morgen, Thomas" in text and "Donnerstag, 29.10." in text
    assert "<b>Dringend</b>" in text and "<b>Beta</b>\nDringendes erledigen. Außerdem offen: Zweites." in text
    assert text.index("Beta") < text.index("Alpha") and "<b>Sonst im Blick</b>" in text
    assert "Gamma" not in text and "Zeta" not in text and "Fertig" not in text
    assert '<a href="http://dash">Mehr im Dashboard</a>' in text


def test_open_pr_makes_quiet_project_active(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "digest.db"))
    db.init()
    with closing(db.db()) as con:
        seed(con)
        text = digest.build_digest(con, TODAY, pushed={}, prs=[{"repo": "o/gamma", "title": "x"}])
    assert "Gamma" in text and "<b>Pull Requests</b>: gamma" in text


def test_plain_strips_markup_and_paths():
    t = digest.plain("**Prod-Deploy** (staging → main): `.env` vorher aus dem Git-Index, `update_db.py` und mehr Text hier")
    assert "`" not in t and "*" not in t and len(t) <= 90
