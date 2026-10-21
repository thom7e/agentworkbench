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
