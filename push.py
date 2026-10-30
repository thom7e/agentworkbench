"""Web Push: VAPID keys live in the settings table, subscriptions in push_subs."""
import base64
import json
from contextlib import closing

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from py_vapid import Vapid
from pywebpush import WebPushException, webpush

import settings
from db import db, now

CLAIMS = {"sub": "mailto:admin@thinkkreativ.de"}


def _private():
    pem = settings.get("vapid_private")
    if not pem:
        key = ec.generate_private_key(ec.SECP256R1())
        pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
        settings.put("vapid_private", pem)
    return pem


def public_key():
    v = Vapid.from_pem(_private().encode())
    raw = v.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def subscribe(sub):
    with closing(db()) as con:
        con.execute("INSERT INTO push_subs(endpoint,p256dh,auth,created) VALUES(?,?,?,?) ON CONFLICT(endpoint) DO UPDATE SET "
                    "p256dh=excluded.p256dh, auth=excluded.auth",
                    (sub["endpoint"], sub["keys"]["p256dh"], sub["keys"]["auth"], now()))
        con.commit()


def send(title, body, url="/"):
    """Send a notification to every subscribed device; dead subscriptions are removed. Returns the number delivered."""
    sent = 0
    with closing(db()) as con:
        for s in con.execute("SELECT * FROM push_subs").fetchall():
            try:
                webpush({"endpoint": s["endpoint"], "keys": {"p256dh": s["p256dh"], "auth": s["auth"]}},
                        json.dumps({"title": title, "body": body, "url": url}), vapid_private_key=Vapid.from_pem(_private().encode()), vapid_claims=dict(CLAIMS))
                sent += 1
            except WebPushException as e:
                if e.response is not None and e.response.status_code in (404, 410):
                    con.execute("DELETE FROM push_subs WHERE id=?", (s["id"],))
                    con.commit()
                else:
                    print("push error:", e, e.response.text if e.response is not None else "", flush=True)
    return sent
