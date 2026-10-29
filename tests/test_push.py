from contextlib import closing

import db
import push


def test_vapid_key_is_stable_and_subscription_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "p.db"))
    db.init()
    key = push.public_key()
    assert len(key) == 87 and push.public_key() == key
    push.subscribe({"endpoint": "https://push.example/1", "keys": {"p256dh": "a", "auth": "b"}})
    push.subscribe({"endpoint": "https://push.example/1", "keys": {"p256dh": "c", "auth": "d"}})
    with closing(db.db()) as con:
        rows = con.execute("SELECT p256dh FROM push_subs").fetchall()
    assert [r[0] for r in rows] == ["c"]


def test_send_counts_and_drops_gone_subscriptions(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "p.db"))
    db.init()
    for n in (1, 2):
        push.subscribe({"endpoint": f"https://push.example/{n}", "keys": {"p256dh": "a", "auth": "b"}})

    class Resp:
        status_code = 410

    def fake(sub, data, **kw):
        if sub["endpoint"].endswith("2"):
            raise push.WebPushException("gone", response=Resp())

    monkeypatch.setattr(push, "webpush", fake)
    assert push.send("t", "b") == 1
    with closing(db.db()) as con:
        assert con.execute("SELECT COUNT(*) FROM push_subs").fetchone()[0] == 1
