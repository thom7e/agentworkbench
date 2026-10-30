import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["AGENTWORKBENCH_DB"] = os.path.join(_tmp, "test.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402

PASSWORD = "correct horse battery"


@pytest.fixture(scope="module")
def client():
    with TestClient(app, follow_redirects=False) as c:
        yield c


def test_first_run_redirects_to_setup(client):
    r = client.get("/")
    assert r.status_code == 303 and r.headers["location"] == "/setup"


def test_setup_validates_and_logs_in(client):
    r = client.post("/setup", data={"password": "short", "repeat": "short"})
    assert r.status_code == 200
    r = client.post("/setup", data={"password": PASSWORD, "repeat": PASSWORD})
    assert r.status_code == 303 and "session" in r.cookies
    assert client.get("/setup").status_code == 303


def test_requires_login_after_logout(client):
    client.post("/logout")
    client.cookies.clear()
    assert client.get("/").status_code == 303
    r = client.post("/login", data={"password": "wrong password"})
    assert r.status_code == 200
    assert "data-fixed" in client.get("/login").text
    r = client.post("/login", data={"password": PASSWORD, "next": "/"})
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert client.get("/login?next=/p/demo-app").headers["location"] == "/p/demo-app"


def test_api_requires_token(client):
    saved = dict(client.cookies)
    client.cookies.clear()
    assert client.get("/api/overview").status_code == 401
    client.cookies.update(saved)


def test_admin_project_and_token_flow(client):
    r = client.post("/admin/projects", data={"name": "Demo App", "area": "Allgemein", "status": "aktiv"})
    assert r.status_code == 303 and r.headers["location"].startswith("/admin/projects/demo-app")
    r = client.post("/admin/tokens", data={"name": "claude"})
    token = r.text.split('class="token">')[1].split("<")[0]
    assert token.startswith("wb_")

    headers = {"Authorization": f"Bearer {token}"}
    other = TestClient(app, follow_redirects=False)
    assert other.get("/api/overview", headers=headers).status_code == 200
    r = other.post("/api/projects/demo-app/todos", json={"text": "Write docs", "prio": 1}, headers=headers)
    assert r.status_code == 200
    brief = other.get("/api/projects/demo-app", headers=headers).text
    assert "Write docs" in brief and "(P1)" in brief
    assert other.get("/api/overview", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_agent_todo_lands_in_inbox_until_seen(client):
    html = client.get("/").text
    assert "Write docs" in html
    tid = int(html.split("/t/")[1].split("/")[0])
    client.post(f"/t/{tid}/seen", data={"next": "/"})
    assert "Neue Aufgaben" not in client.get("/").text


def test_inbox_item_can_be_marked_finished(client):
    other = TestClient(app, follow_redirects=False)
    token = client.post("/admin/tokens", data={"name": "t2"}).text.split('class="token">')[1].split("<")[0]
    r = other.post("/api/projects/demo-app/todos", json={"text": "Already done thing"},
                   headers={"Authorization": f"Bearer {token}"})
    tid = r.json()["id"]
    assert "Already done thing" in client.get("/").text
    client.post(f"/t/{tid}/finished", data={"next": "/"})
    html = client.get("/p/demo-app").text
    assert "Already done thing" in html
    assert f"/t/{tid}/" not in client.get("/").text  # finished: no longer an open task or inbox entry


def test_patch_project_and_multiple_notes(client):
    token = client.post("/admin/tokens", data={"name": "t3"}).text.split('class="token">')[1].split("<")[0]
    other = TestClient(app, follow_redirects=False)
    h = {"Authorization": f"Bearer {token}"}
    r = other.patch("/api/projects/demo-app", json={"vault_note": "notes/a\nhttps://example.com/b"}, headers=h)
    assert r.status_code == 200
    html = client.get("/p/demo-app").text
    assert "https://example.com/b" in html
    assert "Demo App" in html


def test_notes_memory_and_search(client):
    token = client.post("/admin/tokens", data={"name": "t4"}).text.split('class="token">')[1].split("<")[0]
    other = TestClient(app, follow_redirects=False)
    h = {"Authorization": f"Bearer {token}"}
    r = other.post("/api/projects/demo-app/notes", json={"text": "Decided: use SQLite, not Postgres", "pinned": True}, headers=h)
    assert r.status_code == 200
    other.post("/api/projects/demo-app/notes", json={"text": "Older detail about caching"}, headers=h)
    brief = other.get("/api/projects/demo-app", headers=h).text
    assert "## Pinned notes" in brief and "use SQLite" in brief and "caching" in brief
    client.post("/p/demo-app/notes", data={"text": "Own note from the UI"})
    page = client.get("/p/demo-app").text
    assert "Own note from the UI" in page and "angepinnt" in page
    assert "SQLite" in client.get("/search?q=SQLite").text
    assert "SQLite" in other.get("/api/search?q=SQLite", headers=h).text
    assert "use SQLite" in other.get("/export/notes.md", headers=h).text


def test_docs_render_edit_and_sanitize(client):
    token = client.post("/admin/tokens", data={"name": "t5"}).text.split('class="token">')[1].split("<")[0]
    other = TestClient(app, follow_redirects=False)
    h = {"Authorization": f"Bearer {token}"}
    r = other.post("/api/projects/demo-app/docs", json={"title": "Runbook", "body": "# Steps\n\n- one\n\n<script>alert(1)</script>"}, headers=h)
    did = r.json()["id"]
    page = client.get("/p/demo-app").text
    assert "Runbook" in page and "<h1>Steps</h1>" in page and "<script>alert" not in page
    client.post(f"/d/{did}/save", data={"title": "Runbook v2", "body": "changed text"})
    assert "Runbook v2" in client.get("/p/demo-app").text
    assert "changed text" in other.get(f"/api/docs/{did}", headers=h).text
    assert "Documents" in other.get("/api/projects/demo-app", headers=h).text
    client.post(f"/d/{did}/delete")
    assert "Runbook v2" not in client.get("/p/demo-app").text


def test_proxmox_status_ip_and_hide_stopped(client, monkeypatch):
    import proxmox

    guests_raw = [
        {"vmid": 137, "name": "buecher", "node": "pve", "type": "lxc", "status": "running", "cpu": 0.02,
         "mem": 300 * 1024 ** 2, "maxmem": 768 * 1024 ** 2, "uptime": 90000},
        {"vmid": 201, "name": "holtei-app", "node": "pve", "type": "lxc", "status": "stopped", "cpu": 0,
         "mem": 0, "maxmem": 512 * 1024 ** 2, "uptime": 0},
        {"vmid": 150, "name": "ohne-projekt", "node": "thom7e", "type": "lxc", "status": "running", "cpu": 0,
         "mem": 1, "maxmem": 2, "uptime": 5},
    ]

    def fake(path):
        if path.startswith("/cluster/resources"):
            return guests_raw
        if path.endswith("/config"):
            vmid = path.split("/")[-2]
            return {"net0": f"name=eth0,bridge=vmbr0,ip=192.168.178.{int(vmid) % 200},type=veth"}
        return []

    monkeypatch.setattr(proxmox, "_request", fake)
    proxmox._cache.clear()
    client.post("/admin/settings", data={
        "site_title": "T", "language": "de", "areas": "Allgemein", "dormant_days": 90, "default_sort": "aktuell",
        "github_owner": "", "github_token": "", "obsidian_vault": "",
        "proxmox_url": "https://pve.example:8006", "proxmox_token_id": "u@pve!t", "proxmox_token_secret": "secret"})
    client.post("/admin/projects", data={"name": "Bibliothek", "area": "Allgemein", "vmid": 137})
    client.post("/admin/projects", data={"name": "Holtei App", "area": "Allgemein", "vmid": 201})
    page = client.get("/").text
    assert "Container und VMs" in page and "ohne-projekt" in page and "Projekt anlegen" in page
    assert 'class="dot on"' in page and 'class="dot off"' in page
    hidden = client.get("/?hide_stopped=1").text
    assert 'href="/p/holtei-app"' not in hidden and 'href="/p/bibliothek"' in hidden
    proj = client.get("/p/bibliothek").text
    assert "Läuft auf" in proj and "192.168.178.137" in proj
    token = client.post("/admin/tokens", data={"name": "t6"}).text.split('class="token">')[1].split("<")[0]
    brief = TestClient(app).get("/api/projects/bibliothek", headers={"Authorization": f"Bearer {token}"}).text
    assert "Runs on: LXC 137 buecher" in brief
    proxmox._cache.clear()


def test_patch_todo_moves_between_projects(client):
    token = client.post("/admin/tokens", data={"name": "t7"}).text.split('class="token">')[1].split("<")[0]
    h = {"Authorization": f"Bearer {token}"}
    other = TestClient(app)
    client.post("/admin/projects", data={"name": "Target", "area": "Allgemein"})
    tid = other.post("/api/projects/demo-app/todos", json={"text": "Move me"}, headers=h).json()["id"]
    assert other.patch(f"/api/todos/{tid}", json={"project": "target", "prio": 1}, headers=h).status_code == 200
    assert "Move me" in other.get("/api/projects/target", headers=h).text
    assert other.patch(f"/api/todos/{tid}", json={"project": "nope"}, headers=h).status_code == 404


def test_cross_origin_post_is_blocked(client):
    r = client.post("/logout", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


def test_markdown_import_and_json_export(client):
    md = "## Imported\n- [ ] open task\n- [x] finished task\n"
    client.post("/admin/import.md", data={"markdown": md})
    data = client.get("/admin/export.json").json()
    assert any(p["slug"] == "imported" for p in data["projects"])
    assert {t["text"] for t in data["todos"] if t["project"] == "imported"} == {"open task", "finished task"}


def test_settings_roundtrip(client):
    client.post("/admin/settings", data={
        "site_title": "My Board", "language": "en", "areas": "Work\nHome", "dormant_days": 30,
        "default_sort": "offen", "github_owner": "", "github_token": "", "obsidian_vault": "",
    })
    html = client.get("/").text
    assert "My Board" in html


def test_english_ui_after_language_switch(client):
    html = client.get("/").text
    assert "Tasks by priority" in html and "Aufgaben nach" not in html
    assert '<html lang="en">' in html


def test_demo_seed_creates_a_complete_dashboard(tmp_path, monkeypatch):
    import subprocess
    import sys
    env = {**os.environ, "AGENTWORKBENCH_DB": str(tmp_path / "demo.db")}
    out = subprocess.run([sys.executable, "scripts/demo_seed.py"], env=env, capture_output=True, text=True)
    assert out.returncode == 0 and "demo-password-123" in out.stdout
    again = subprocess.run([sys.executable, "scripts/demo_seed.py"], env=env, capture_output=True, text=True)
    assert again.returncode != 0


def test_live_toggle_shows_badge(client):
    assert 'class="live"' not in client.get("/").text
    assert client.post("/p/demo-app/live", data={"live": "1"}).status_code == 303
    assert 'class="live"' in client.get("/").text and "checked" in client.get("/p/demo-app").text
    client.post("/p/demo-app/live", data={})
    assert 'class="live"' not in client.get("/").text


def test_pwa_files_and_quick_add(client):
    sw = client.get("/sw.js")
    assert sw.status_code == 200 and sw.headers["service-worker-allowed"] == "/"
    assert "__V__" not in sw.text and "awb-" in sw.text
    html = client.get("/").text
    assert 'id="qa"' in html and "/static/app.js?v=" in html and "/static/style.css?v=" in html and 'value="demo-app"' in html
    assert client.post("/p/demo-app/add", data={"text": "Per Schnell-Eintrag", "prio": "2", "kind": "todo"}).status_code == 303
    assert "Per Schnell-Eintrag" in client.get("/").text
    assert "agentworkbench://run?project=demo-app" in client.get("/").text


def test_briefing_page_and_toggle_returns_there(client):
    page = client.get("/briefing").text
    assert "Guten Morgen, Thomas" in page and "brief-projects" in page and 'action="/p/demo-app/live"' in page
    r = client.post("/p/demo-app/live", data={"live": "1", "next": "/briefing"})
    assert r.status_code == 303 and r.headers["location"] == "/briefing"
    client.post("/p/demo-app/live", data={"next": "/briefing"})


class SoftAuthenticator:
    """Minimal software passkey (ES256, 'none' attestation) to run the real WebAuthn verification in tests."""

    def __init__(self, rp_id="testserver"):
        import hashlib

        from cryptography.hazmat.primitives.asymmetric import ec

        self.key = ec.generate_private_key(ec.SECP256R1())
        self.cred_id = b"cred-" + hashlib.sha256(rp_id.encode()).digest()[:10]
        self.rp_hash = hashlib.sha256(rp_id.encode()).digest()
        self.count = 0

    @staticmethod
    def b64(raw):
        import base64

        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    def client_data(self, kind, challenge_b64, origin="https://testserver"):
        import json

        return json.dumps({"type": kind, "challenge": challenge_b64, "origin": origin}).encode()

    def register(self, challenge_b64):
        import cbor2

        nums = self.key.public_key().public_numbers()
        cose = cbor2.dumps({1: 2, 3: -7, -1: 1, -2: nums.x.to_bytes(32, "big"), -3: nums.y.to_bytes(32, "big")})
        auth_data = self.rp_hash + bytes([0x45]) + (0).to_bytes(4, "big") + bytes(16) + len(self.cred_id).to_bytes(2, "big") + self.cred_id + cose
        att = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
        return {"id": self.b64(self.cred_id), "rawId": self.b64(self.cred_id), "type": "public-key",
                "response": {"clientDataJSON": self.b64(self.client_data("webauthn.create", challenge_b64)), "attestationObject": self.b64(att)}}

    def assert_(self, challenge_b64):
        import hashlib

        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec

        self.count += 1
        auth_data = self.rp_hash + bytes([0x05]) + self.count.to_bytes(4, "big")
        cd = self.client_data("webauthn.get", challenge_b64)
        sig = self.key.sign(auth_data + hashlib.sha256(cd).digest(), ec.ECDSA(hashes.SHA256()))
        return {"id": self.b64(self.cred_id), "rawId": self.b64(self.cred_id), "type": "public-key",
                "response": {"clientDataJSON": self.b64(cd), "authenticatorData": self.b64(auth_data), "signature": self.b64(sig)}}


def test_passkey_register_and_login_roundtrip(client):
    anon = TestClient(app, follow_redirects=False)
    assert anon.get("/passkey/register/options").status_code == 303  # needs a session
    dev = SoftAuthenticator()
    opts = client.get("/passkey/register/options").json()
    assert opts["rp"]["id"] == "testserver" and opts["authenticatorSelection"]["residentKey"] == "required"
    assert client.post("/passkey/register/verify", json={"credential": {"id": "x"}}).status_code == 400
    opts = client.get("/passkey/register/options").json()
    r = client.post("/passkey/register/verify", json={"credential": dev.register(opts["challenge"]), "name": "Test-Gerät"})
    assert r.status_code == 200, r.text
    assert "Test-Gerät" in client.get("/admin/settings").text

    opts = anon.get("/passkey/login/options").json()  # public
    r = anon.post("/passkey/login/verify", json={"credential": dev.assert_(opts["challenge"])})
    assert r.status_code == 200 and "session" in r.cookies
    assert anon.get("/").status_code == 200
    # replaying the same assertion must fail (challenge is bound to the cookie, counter must rise)
    other = TestClient(app, follow_redirects=False)
    other.get("/passkey/login/options")
    assert other.post("/passkey/login/verify", json={"credential": dev.assert_("AAAA")}).status_code in (400, 401)
    stranger = TestClient(app, follow_redirects=False)
    opts = stranger.get("/passkey/login/options").json()
    bad = SoftAuthenticator()
    assert stranger.post("/passkey/login/verify", json={"credential": bad.assert_(opts["challenge"])}).status_code == 401
    pid = int(client.get("/admin/settings").text.split("/passkey/")[1].split("/")[0])
    assert client.post(f"/passkey/{pid}/delete").status_code == 204


def test_fresh_design_is_default_and_classic_is_a_cookie(client):
    page = client.get("/").text
    assert 'class="has-side"' in page and 'class="side"' in page and "/static/fresh.css?v=" in page
    assert client.get("/design/classic").status_code == 303
    assert 'class="side"' not in client.get("/").text
    client.get("/design/fresh")
    assert 'class="side"' in client.get("/").text


def test_project_page_has_tabs(client):
    page = client.get("/p/demo-app").text
    for name in ("tasks", "notes", "docs", "log"):
        assert f'data-ptab-link="{name}"' in page and f'data-ptab="{name}"' in page
