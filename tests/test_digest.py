from contextlib import closing
from datetime import datetime

import db  # noqa: E402
import digest  # noqa: E402


def test_build_digest_sections(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "digest.db"))
    db.init()
    with closing(db.db()) as con:
        con.execute("INSERT INTO projects(slug,name) VALUES('a','Alpha')")
        con.execute("INSERT INTO todos(project,text,prio,created) VALUES('a','Dringendes',1,'2026-10-20 10:00')")
        con.execute("INSERT INTO todos(project,text,prio,done,created,done_at) VALUES('a','Fertig',2,1,'2026-10-20 10:00','2026-10-28 09:00')")
        con.execute("INSERT INTO todos(project,text,kind,created) VALUES('a','Idee X','idee','2026-10-28 08:00')")
        con.execute("INSERT INTO activity(project,text,ts) VALUES('a','Deploy','2026-10-28 12:00')")
        con.commit()
        text = digest.build_digest(con, datetime(2026, 10, 29, 7, 0))
    assert "Donnerstag, 29.10." in text
    assert "Dringend (P1): 1" in text and "Alpha: Dringendes" in text
    assert "Gestern erledigt: 1" in text and "Alpha: Deploy" in text
    assert "Neue Ideen: 1" in text
    assert "Ruhend" not in text
