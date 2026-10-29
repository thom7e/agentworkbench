from contextlib import closing

import bot
import db


def test_keyboard_lists_relevant_projects_and_toggle_flips_live(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "bot.db"))
    db.init()
    with closing(db.db()) as con:
        con.execute("INSERT INTO projects(slug,name,live) VALUES('a','Alpha',1)")
        con.execute("INSERT INTO projects(slug,name) VALUES('b','Beta')")
        con.execute("INSERT INTO projects(slug,name) VALUES('c','Ohne Todos')")
        con.execute("INSERT INTO projects(slug,name,status) VALUES('z','Archiv','archiv')")
        con.execute("INSERT INTO todos(project,text,prio,created) VALUES('b','x',2,'2026-10-29 07:00')")
        con.execute("INSERT INTO todos(project,text,prio,created) VALUES('z','x',1,'2026-10-29 07:00')")
        con.commit()
        rows = bot.keyboard(con)["inline_keyboard"]
        assert [r[0]["text"] for r in rows] == ["✅ Alpha", "▫️ Beta"]
        assert rows[1][0]["callback_data"] == "t:b"
        bot.toggle(con, "b")
        bot.toggle(con, "a")
        assert [r[0]["text"] for r in bot.keyboard(con)["inline_keyboard"]] == ["✅ Beta"]
