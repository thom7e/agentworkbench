from contextlib import closing
from datetime import datetime

import db
import digest


def test_build_digest_groups_by_project_and_hides_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "digest.db"))
    db.init()
    with closing(db.db()) as con:
        con.execute("INSERT INTO projects(slug,name) VALUES('a','Alpha')")
        con.execute("INSERT INTO projects(slug,name) VALUES('b','Beta')")
        con.execute("INSERT INTO projects(slug,name,status) VALUES('z','Zeta','archiv')")
        con.execute("INSERT INTO todos(project,text,prio,created) VALUES('a','Normales',2,'2026-10-20 10:00')")
        con.execute("INSERT INTO todos(project,text,short,prio,created) VALUES('b','**Lang** `x`: Details',"
                    "'Dringendes erledigen',1,'2026-10-20 10:00')")
        con.execute("INSERT INTO todos(project,text,prio,created) VALUES('z','Altlast',1,'2026-10-20 10:00')")
        con.execute("INSERT INTO todos(project,text,prio,done,created) VALUES('a','Fertig',1,1,'2026-10-20 10:00')")
        con.commit()
        text = digest.build_digest(con, datetime(2026, 10, 29, 7, 0))
    assert "Donnerstag, 29.10." in text and "1 dringend" in text
    assert text.index("Beta") < text.index("Alpha")
    assert "! Dringendes erledigen" in text and "· Normales" in text
    assert "Zeta" not in text and "Fertig" not in text


def test_plain_strips_markup_and_paths():
    t = digest.plain("**Prod-Deploy** (staging → main): `.env` vorher aus dem Git-Index, `update_db.py` und mehr Text hier")
    assert "`" not in t and "*" not in t and len(t) <= 90
