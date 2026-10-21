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
    r = client.post("/login", data={"password": PASSWORD, "next": "/"})
    assert r.status_code == 303


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
    assert "Already done thing" not in client.get("/").text.split("Aufgaben nach")[0]


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
    assert "Holtei App" not in hidden and "Bibliothek" in hidden
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
