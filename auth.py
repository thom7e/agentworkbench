import hashlib
import hmac
import os
import secrets
import time
from contextlib import closing
from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from itsdangerous import BadSignature, URLSafeTimedSerializer

import settings
from db import db, now

COOKIE = "session"
MAX_AGE = 60 * 60 * 24 * 30
ENV_TOKEN = os.environ.get("AGENTWORKBENCH_TOKEN", "")
SECURE_COOKIE = os.environ.get("AGENTWORKBENCH_COOKIE_SECURE", "0") == "1"
PUBLIC_PREFIXES = ("/static", "/login", "/setup", "/healthz")
API_PREFIXES = ("/api", "/export")

_fails = {}


def hash_password(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.scrypt(pw.encode(), salt=salt.encode(), n=2**14, r=8, p=1).hex()
    return f"scrypt${salt}${h}"


def check_password(pw, stored):
    try:
        _, salt, _ = stored.split("$")
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(pw, salt), stored)


def admin_exists():
    return bool(settings.get("admin_hash"))


def _serializer():
    key = settings.get("secret_key")
    if not key:
        key = secrets.token_hex(32)
        settings.put("secret_key", key)
    return URLSafeTimedSerializer(key)


def make_session():
    return _serializer().dumps({"admin": True})


def valid_session(request):
    raw = request.cookies.get(COOKIE)
    if not raw:
        return False
    try:
        return bool(_serializer().loads(raw, max_age=MAX_AGE).get("admin"))
    except BadSignature:
        return False


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_token(name):
    token = "wb_" + secrets.token_urlsafe(32)
    with closing(db()) as con:
        con.execute("INSERT INTO api_tokens(name,token_hash,created) VALUES(?,?,?)",
                    (name, token_hash(token), now()))
        con.commit()
    return token


def valid_bearer(request):
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        return False
    token = header[7:]
    if ENV_TOKEN and hmac.compare_digest(token, ENV_TOKEN):
        return True
    with closing(db()) as con:
        row = con.execute("SELECT id FROM api_tokens WHERE token_hash=?", (token_hash(token),)).fetchone()
        if row:
            con.execute("UPDATE api_tokens SET last_used=? WHERE id=?", (now(), row["id"]))
            con.commit()
    return bool(row)


def login_allowed(ip):
    recent = [t for t in _fails.get(ip, []) if time.time() - t < 600]
    _fails[ip] = recent
    return len(recent) < 10


def login_failed(ip):
    _fails.setdefault(ip, []).append(time.time())
    time.sleep(1)


def same_origin(request):
    origin = request.headers.get("origin")
    if not origin or origin == "null":
        return True
    return urlparse(origin).netloc == request.headers.get("host", "")


async def middleware(request: Request, call_next):
    path = request.url.path
    if request.method not in ("GET", "HEAD", "OPTIONS") and not path.startswith(API_PREFIXES):
        if not same_origin(request):
            return JSONResponse({"detail": "cross-origin request blocked"}, status_code=403)
    if path.startswith(PUBLIC_PREFIXES):
        return await call_next(request)
    if path.startswith(API_PREFIXES):
        if valid_bearer(request) or valid_session(request):
            return await call_next(request)
        return JSONResponse({"detail": "unauthorized"}, status_code=401)
    if not admin_exists():
        return RedirectResponse("/setup", status_code=303)
    if not valid_session(request):
        return RedirectResponse(f"/login?next={path}", status_code=303)
    return await call_next(request)
