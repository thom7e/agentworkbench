"""Passkey (WebAuthn) login as an alternative to the password. One admin, several passkeys (one per device)."""
import base64
import json
from contextlib import closing
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from itsdangerous import BadSignature
from webauthn import (generate_authentication_options, generate_registration_options, options_to_json,
                      verify_authentication_response, verify_registration_response)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (AuthenticatorSelectionCriteria, PublicKeyCredentialDescriptor,
                                      ResidentKeyRequirement, UserVerificationRequirement)

import auth
from db import db, now

router = APIRouter(prefix="/passkey")
RP_NAME = "AgentWorkbench"
CHALLENGE_COOKIE = "pk_challenge"
CHALLENGE_MAX_AGE = 300


def relying_party(request):
    """RP id and origin from the host the browser used (works behind the Cloudflare tunnel and on localhost)."""
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    hostname = host.split(":")[0]
    local = hostname in ("localhost", "127.0.0.1")
    scheme = request.url.scheme if local else "https"
    return hostname, f"{scheme}://{host}"


def set_challenge(resp, challenge, purpose):
    token = auth._serializer().dumps({"c": bytes_to_base64url(challenge), "p": purpose})
    resp.set_cookie(CHALLENGE_COOKIE, token, max_age=CHALLENGE_MAX_AGE, httponly=True, samesite="strict",
                    secure=auth.SECURE_COOKIE)


def take_challenge(request, purpose):
    try:
        data = auth._serializer().loads(request.cookies.get(CHALLENGE_COOKIE, ""), max_age=CHALLENGE_MAX_AGE)
    except BadSignature:
        raise HTTPException(400, "challenge missing or expired")
    if data.get("p") != purpose:
        raise HTTPException(400, "wrong challenge")
    return base64url_to_bytes(data["c"])


def json_options(options, purpose):
    resp = Response(options_to_json(options), media_type="application/json")
    set_challenge(resp, options.challenge, purpose)
    return resp


def stored():
    with closing(db()) as con:
        return con.execute("SELECT * FROM passkeys ORDER BY id").fetchall()


@router.get("/register/options")
def register_options(request: Request):
    rp_id, _ = relying_party(request)
    options = generate_registration_options(
        rp_id=rp_id, rp_name=RP_NAME, user_name="admin", user_id=b"admin", user_display_name="Admin",
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED, user_verification=UserVerificationRequirement.REQUIRED),
        exclude_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(p["cred_id"])) for p in stored()])
    return json_options(options, "register")


@router.post("/register/verify")
async def register_verify(request: Request):
    body = await request.json()
    rp_id, origin = relying_party(request)
    try:
        verified = verify_registration_response(credential=body["credential"], expected_challenge=take_challenge(request, "register"),
                                                expected_rp_id=rp_id, expected_origin=origin, require_user_verification=True)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "registration failed")
    with closing(db()) as con:
        con.execute("INSERT INTO passkeys(cred_id,public_key,sign_count,name,created) VALUES(?,?,?,?,?)",
                    (bytes_to_base64url(verified.credential_id), bytes_to_base64url(verified.credential_public_key),
                     verified.sign_count, (body.get("name") or "Passkey").strip()[:60], now()))
        con.commit()
    return {"ok": True}


@router.get("/login/options")
def login_options(request: Request):
    rp_id, _ = relying_party(request)
    options = generate_authentication_options(rp_id=rp_id, user_verification=UserVerificationRequirement.REQUIRED)
    return json_options(options, "login")


@router.post("/login/verify")
async def login_verify(request: Request):
    body = await request.json()
    rp_id, origin = relying_party(request)
    challenge = take_challenge(request, "login")
    cred = body.get("credential") or {}
    with closing(db()) as con:
        row = con.execute("SELECT * FROM passkeys WHERE cred_id=?", (cred.get("id", ""),)).fetchone()
        if not row:
            raise HTTPException(401, "unknown passkey")
        try:
            verified = verify_authentication_response(
                credential=cred, expected_challenge=challenge, expected_rp_id=rp_id, expected_origin=origin,
                credential_public_key=base64url_to_bytes(row["public_key"]), credential_current_sign_count=row["sign_count"],
                require_user_verification=True)
        except Exception:
            raise HTTPException(401, "verification failed")
        con.execute("UPDATE passkeys SET sign_count=?, last_used=? WHERE id=?", (verified.new_sign_count, now(), row["id"]))
        con.commit()
    resp = JSONResponse({"ok": True})
    resp.set_cookie(auth.COOKIE, auth.make_session(), max_age=auth.MAX_AGE, httponly=True, samesite="lax",
                    secure=auth.SECURE_COOKIE)
    resp.delete_cookie(CHALLENGE_COOKIE)
    return resp


@router.post("/{pid}/delete")
def delete(pid: int):
    with closing(db()) as con:
        con.execute("DELETE FROM passkeys WHERE id=?", (pid,))
        con.commit()
    return Response(status_code=204)
