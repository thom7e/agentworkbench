import json
import re
from contextlib import closing

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response

import auth
import github
import settings
from db import db, now
from render import slugify, templates

router = APIRouter(prefix="/admin")
STATUSES = ("aktiv", "pause", "archiv")


def page(request, name, **ctx):
    return templates.TemplateResponse(request, name, ctx)


def back(path, msg=""):
    return RedirectResponse(path + (f"?msg={msg}" if msg else ""), status_code=303)


@router.get("")
def home():
    return RedirectResponse("/admin/settings", status_code=303)


# ---- Einstellungen ----

@router.get("/settings", response_class=HTMLResponse)
def settings_form(request: Request, msg: str = ""):
    return page(request, "admin_settings.html", tab="settings", msg=msg,
                s={k: settings.get(k) for k in settings.DEFAULTS if k != "github_token"},
                areas="\n".join(settings.areas()), has_token=bool(settings.get("github_token")))


@router.post("/settings")
def settings_save(
    site_title: str = Form(...), language: str = Form("de"), areas: str = Form(""),
    dormant_days: int = Form(90), default_sort: str = Form("aktuell"),
    github_owner: str = Form(""), github_token: str = Form(""), obsidian_vault: str = Form(""),
):
    names = [a.strip() for a in areas.splitlines() if a.strip()]
    settings.put("site_title", site_title.strip() or "AgentWorkbench")
    settings.put("language", language if language in ("de", "en") else "de")
    settings.put("areas", json.dumps(names or ["Allgemein"]))
    settings.put("dormant_days", str(max(1, dormant_days)))
    settings.put("default_sort", default_sort if default_sort in ("aktuell", "offen") else "aktuell")
    settings.put("github_owner", github_owner.strip())
    if github_token.strip():
        settings.put("github_token", github_token.strip())
    settings.put("obsidian_vault", obsidian_vault.strip())
    return back("/admin/settings", "saved")


# ---- Projekte ----

@router.get("/projects", response_class=HTMLResponse)
def projects_list(request: Request):
    with closing(db()) as con:
        rows = con.execute(
            "SELECT p.*, (SELECT COUNT(*) FROM todos t WHERE t.project=p.slug AND t.done=0) AS open_n "
            "FROM projects p ORDER BY p.status, p.area, p.name"
        ).fetchall()
    return page(request, "admin_projects.html", tab="projects", rows=rows)


@router.get("/projects/new", response_class=HTMLResponse)
def project_new(request: Request):
    blank = {"slug": "", "name": "", "status": "aktiv", "area": "", "deploy": "", "stack": "",
             "summary": "", "repo": "", "wiki": "", "vault_note": ""}
    return project_form(request, blank, True)


@router.get("/projects/{slug}", response_class=HTMLResponse)
def project_edit(request: Request, slug: str, msg: str = ""):
    with closing(db()) as con:
        p = con.execute("SELECT * FROM projects WHERE slug=?", (slug,)).fetchone()
    if not p:
        raise HTTPException(404)
    return project_form(request, p, False, msg)


def project_form(request, p, is_new, msg=""):
    repos = [r["full_name"] for r in github.list_repos()]
    return page(request, "admin_project.html", tab="projects", p=p, is_new=is_new, msg=msg,
                areas=settings.areas(), statuses=STATUSES, repos=repos)


@router.post("/projects")
def project_save(
    name: str = Form(...), slug: str = Form(""), original: str = Form(""), status: str = Form("aktiv"),
    area: str = Form(""), deploy: str = Form(""), stack: str = Form(""), summary: str = Form(""),
    repo: str = Form(""), wiki: str = Form(""), vault_note: str = Form(""),
):
    if status not in STATUSES:
        raise HTTPException(400)
    slug = original or slugify(slug or name)
    with closing(db()) as con:
        exists = con.execute("SELECT 1 FROM projects WHERE slug=?", (slug,)).fetchone()
        if exists and not original:
            raise HTTPException(409, "slug exists")
        values = (name.strip(), status, area, deploy.strip(), stack.strip(), summary.strip(),
                  vault_note.strip(), repo.strip(), wiki.strip())
        if original:
            con.execute("UPDATE projects SET name=?,status=?,area=?,deploy=?,stack=?,summary=?,vault_note=?,"
                        "repo=?,wiki=? WHERE slug=?", values + (slug,))
        else:
            con.execute("INSERT INTO projects(name,status,area,deploy,stack,summary,vault_note,repo,wiki,slug) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?)", values + (slug,))
        con.commit()
    return back(f"/admin/projects/{slug}", "saved")


@router.post("/projects/{slug}/delete")
def project_delete(slug: str, confirm: str = Form("")):
    if not confirm:
        raise HTTPException(400)
    with closing(db()) as con:
        con.execute("DELETE FROM projects WHERE slug=?", (slug,))
        con.commit()
    return back("/admin/projects")


# ---- API-Zugänge ----

@router.get("/tokens", response_class=HTMLResponse)
def tokens(request: Request, new: str = ""):
    with closing(db()) as con:
        rows = con.execute("SELECT * FROM api_tokens ORDER BY id DESC").fetchall()
    return page(request, "admin_tokens.html", tab="tokens", rows=rows, new=new)


@router.post("/tokens")
def token_create(request: Request, name: str = Form(...)):
    token = auth.create_token(name.strip())
    return page(request, "admin_tokens.html", tab="tokens", new=token, rows=_tokens())


def _tokens():
    with closing(db()) as con:
        return con.execute("SELECT * FROM api_tokens ORDER BY id DESC").fetchall()


@router.post("/tokens/{tid}/revoke")
def token_revoke(tid: int):
    with closing(db()) as con:
        con.execute("DELETE FROM api_tokens WHERE id=?", (tid,))
        con.commit()
    return back("/admin/tokens")


# ---- Daten ----

@router.get("/data", response_class=HTMLResponse)
def data_page(request: Request, p: int = -1, tasks: int = -1):
    return page(request, "admin_data.html", tab="data", imported=(p, tasks) if p >= 0 else None)


@router.get("/export.json")
def export_json():
    with closing(db()) as con:
        data = {name: [dict(r) for r in con.execute(f"SELECT * FROM {name}")]
                for name in ("projects", "todos", "activity")}
    return Response(json.dumps(data, ensure_ascii=False, indent=2), media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="backup.json"'})


@router.post("/import.json")
async def import_json(file: UploadFile = File(...)):
    try:
        data = json.loads((await file.read()).decode("utf-8"))
        projects, todos, activity = data["projects"], data["todos"], data.get("activity", [])
    except (ValueError, KeyError, UnicodeDecodeError):
        raise HTTPException(400, "invalid backup file")
    with closing(db()) as con:
        for p in projects:
            cols = [c for c in p if c in ("slug", "name", "status", "area", "deploy", "stack", "summary",
                                         "vault_note", "repo", "wiki", "sort")]
            con.execute(f"INSERT OR REPLACE INTO projects({','.join(cols)}) VALUES({','.join('?' * len(cols))})",
                        [p[c] for c in cols])
        for t in todos:
            cols = [c for c in t if c in ("project", "text", "kind", "prio", "done", "created", "done_at",
                                         "source", "seen")]
            con.execute(f"INSERT INTO todos({','.join(cols)}) VALUES({','.join('?' * len(cols))})",
                        [t[c] for c in cols])
        for a in activity:
            con.execute("INSERT INTO activity(project,text,ts) VALUES(?,?,?)", (a["project"], a["text"], a["ts"]))
        con.commit()
    return back(f"/admin/data?p={len(projects)}&tasks={len(todos)}")


@router.post("/import.md")
def import_md(markdown: str = Form(...)):
    n_p = n_t = 0
    slug = None
    with closing(db()) as con:
        for line in markdown.splitlines():
            if line.startswith("## "):
                name = line[3:].strip()
                slug = slugify(name)
                cur = con.execute("INSERT OR IGNORE INTO projects(slug,name) VALUES(?,?)", (slug, name))
                n_p += cur.rowcount
                continue
            m = re.match(r"\s*[-*] \[( |x|X)\] (.+)", line)
            if m and slug:
                done = m.group(1) != " "
                con.execute("INSERT INTO todos(project,text,done,created,done_at) VALUES(?,?,?,?,?)",
                            (slug, m.group(2).strip(), int(done), now(), now() if done else None))
                n_t += 1
        con.commit()
    return back(f"/admin/data?p={n_p}&tasks={n_t}")
