from contextlib import closing
from datetime import datetime

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import auth
import digest
import db as database
import github
import proxmox
import push
from i18n import t as tr
import settings
from admin import router as admin_router
from passkeys import router as passkey_router
from db import BASE, db, now
from render import ago_days, templates

database.init()

app = FastAPI(title="AgentWorkbench")
app.middleware("http")(auth.middleware)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/push/key")
def push_key():
    return {"key": push.public_key()}


@app.post("/push/subscribe")
async def push_subscribe(request: Request):
    push.subscribe(await request.json())
    return {"ok": True}


@app.post("/push/test")
def push_test():
    return {"sent": push.send("AgentWorkbench", "Test-Benachrichtigung funktioniert.")}


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    body = (BASE / "static" / "sw.js").read_text(encoding="utf-8").replace("__V__", templates.env.globals["asset_v"])
    return Response(body, media_type="text/javascript", headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})
app.include_router(admin_router)
app.include_router(passkey_router)

WEEKDAYS = {
    "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
MONTHS = {
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September",
           "Oktober", "November", "Dezember"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September",
           "October", "November", "December"],
}


def today_label():
    lang = settings.get("language") if settings.get("language") in WEEKDAYS else "de"
    d = datetime.now()
    wd, mon = WEEKDAYS[lang][d.weekday()], MONTHS[lang][d.month - 1]
    return f"{wd}, {d.day}. {mon}" if lang == "de" else f"{wd}, {mon} {d.day}"


def safe_next(value, default="/"):
    return value if value.startswith("/") and not value.startswith("//") else default


def project_or_404(con, slug):
    p = con.execute("SELECT * FROM projects WHERE slug=?", (slug,)).fetchone()
    if not p:
        raise HTTPException(404, "unknown project")
    return p


def brief(con, slug):
    p = project_or_404(con, slug)
    todos = con.execute(
        "SELECT * FROM todos WHERE project=? ORDER BY done, kind, prio, id", (slug,)
    ).fetchall()
    log = con.execute(
        "SELECT * FROM activity WHERE project=? ORDER BY id DESC LIMIT 8", (slug,)
    ).fetchall()
    out = [f"# {p['name']} ({p['slug']}) — {p['status']}"]
    for k, label in (("deploy", "Deploy"), ("stack", "Stack"), ("repo", "Repo"),
                     ("vault_note", "Linked notes"), ("wiki", "Wiki")):
        if p[k]:
            out.append(f"{label}: {', '.join(p[k].splitlines())}")
    g = proxmox.by_vmid().get(p["vmid"]) if p["vmid"] and proxmox.enabled() else None
    if g:
        out.append(f"Runs on: {g['type'].upper()} {g['vmid']} {g['name']} (node {g['node']}), {g['ip'] or 'no ip'}, {g['status']}")
    if p["summary"]:
        out.append(p["summary"])
    notes = con.execute("SELECT * FROM notes WHERE project=? ORDER BY id DESC", (slug,)).fetchall()
    docs = con.execute("SELECT id,title,updated FROM docs WHERE project=? ORDER BY title", (slug,)).fetchall()
    if docs:
        out.append("\n## Documents (read with GET /api/docs/<id>)")
        out += [f"- #{d['id']} {d['title']} (updated {d['updated']})" for d in docs]
    pinned = [n for n in notes if n["pinned"]]
    recent = [n for n in notes if not n["pinned"]][:5]
    for title, rows in (("Pinned notes", pinned), ("Recent notes", recent)):
        if rows:
            out.append(f"\n## {title}")
            for n in rows:
                out.append(f"### #{n['id']} {n['created']} ({n['author']})\n{n['text']}")
    for kind, title in (("todo", "Open"), ("idee", "Ideas")):
        rows = [t for t in todos if not t["done"] and t["kind"] == kind]
        out.append(f"\n## {title}")
        out += [f"- [ ] #{t['id']} (P{t['prio']}) {t['text']}" for t in rows] or ["- –"]
    out.append("\n## Recently done")
    done = [t for t in todos if t["done"]][-5:]
    out += [f"- [x] #{t['id']} {t['text']} ({t['done_at']})" for t in done] or ["- –"]
    out.append("\n## Log")
    out += [f"- {a['ts']} {a['text']}" for a in log] or ["- –"]
    return "\n".join(out)


# ---------- Setup / Login ----------

@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.get("/setup", response_class=HTMLResponse)
def setup_form(request: Request):
    if auth.admin_exists():
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "setup.html", {"error": ""})


@app.post("/setup")
def setup_save(request: Request, password: str = Form(...), repeat: str = Form(...)):
    if auth.admin_exists():
        raise HTTPException(403)
    error = "password.mismatch" if password != repeat else "password.short" if len(password) < 10 else ""
    if error:
        return templates.TemplateResponse(request, "setup.html", {"error": error})
    settings.put("admin_hash", auth.hash_password(password))
    return start_session("/admin/settings")


def start_session(target):
    resp = RedirectResponse(target, status_code=303)
    resp.set_cookie(auth.COOKIE, auth.make_session(), max_age=auth.MAX_AGE, httponly=True,
                    samesite="lax", secure=auth.SECURE_COOKIE)
    return resp


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request, next: str = "/"):
    if not auth.admin_exists():
        return RedirectResponse("/setup", status_code=303)
    if auth.valid_session(request):
        return RedirectResponse(safe_next(next), status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": "", "next": safe_next(next)})


@app.post("/login")
def login(request: Request, password: str = Form(...), next: str = Form("/")):
    ip = request.client.host if request.client else "?"
    if not auth.login_allowed(ip):
        return templates.TemplateResponse(request, "login.html", {"error": "login.locked", "next": safe_next(next)})
    if not auth.check_password(password, settings.get("admin_hash")):
        auth.login_failed(ip)
        return templates.TemplateResponse(request, "login.html", {"error": "login.fail", "next": safe_next(next)})
    return start_session(safe_next(next))


@app.post("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie(auth.COOKIE)
    return resp


# ---------- Web ----------

@app.get("/", response_class=HTMLResponse)
def index(request: Request, status: str = "aktiv", sort: str = "", hide_stopped: str = ""):
    hide = hide_stopped == "1"
    sort = sort or settings.get("default_sort")
    area_names = settings.areas()
    dormant_days = int(settings.get("dormant_days") or 90)
    with closing(db()) as con:
        projects = con.execute(
            "SELECT p.*, "
            "(SELECT COUNT(*) FROM todos t WHERE t.project=p.slug AND t.done=0 AND t.kind='todo') AS open_n, "
            "(SELECT COUNT(*) FROM todos t WHERE t.project=p.slug AND t.done=0 AND t.kind='idee') AS idea_n, "
            "(SELECT MAX(ts) FROM activity a WHERE a.project=p.slug) AS last_ts "
            "FROM projects p WHERE p.status=? ORDER BY p.sort, p.name",
            (status,),
        ).fetchall()
        pushed = github.pushed_map()
        px = proxmox.by_vmid() if proxmox.enabled() else {}
        groups = {a: {"active": [], "dormant": []} for a in area_names}
        for p in projects:
            g = px.get(p["vmid"]) if p["vmid"] else None
            if hide and g and g["status"] != "running":
                continue
            top = con.execute(
                "SELECT * FROM todos WHERE project=? AND done=0 AND kind='todo' ORDER BY prio, id LIMIT 1",
                (p["slug"],),
            ).fetchone()
            p1 = con.execute(
                "SELECT COUNT(*) FROM todos WHERE project=? AND done=0 AND kind='todo' AND prio=1",
                (p["slug"],),
            ).fetchone()[0]
            last = max(p["last_ts"] or "", pushed.get(p["repo"].lower(), "")[:10].replace("T", " "))
            quiet = status == "aktiv" and p["open_n"] == 0 and (not last or ago_days(last) > dormant_days)
            groups[p["area"] if p["area"] in groups else area_names[0]]["dormant" if quiet else "active"].append(
                (p, top, p1, last, g))
        linked = {}
        for r in con.execute("SELECT slug, name, vmid FROM projects WHERE vmid > 0"):
            linked.setdefault(r["vmid"], []).append(r)
        focus = con.execute(
            "SELECT t.*, p.name AS pname FROM todos t JOIN projects p ON p.slug=t.project "
            "WHERE t.done=0 AND t.kind='todo' AND t.prio=1 AND p.status='aktiv' ORDER BY p.sort, p.name, t.id"
        ).fetchall()
        recent = con.execute(
            "SELECT a.*, p.name AS pname FROM activity a JOIN projects p ON p.slug=a.project "
            "ORDER BY a.id DESC LIMIT 10"
        ).fetchall()
        inbox = con.execute(
            "SELECT t.*, p.name AS pname FROM todos t JOIN projects p ON p.slug=t.project "
            "WHERE t.seen=0 AND t.done=0 ORDER BY t.id DESC"
        ).fetchall()
        brief = digest.summary_counts(con)
        board = {1: [], 2: [], 3: []}
        for t in con.execute(
            "SELECT t.*, p.name AS pname FROM todos t JOIN projects p ON p.slug=t.project "
            "WHERE t.done=0 AND t.kind='todo' AND p.status=? ORDER BY p.sort, p.name, t.id",
            (status,),
        ):
            board[t["prio"]].append(t)
    for grp in groups.values():
        if sort == "offen":
            grp["active"].sort(key=lambda x: (-x[0]["open_n"], -x[2], x[0]["name"].lower()))
        else:
            grp["active"].sort(key=lambda x: (x[3] != "", x[3]), reverse=True)
        grp["dormant"].sort(key=lambda x: x[0]["name"].lower())
    guest_rows = [g for g in px.values() if not (hide and g["status"] != "running")]
    return templates.TemplateResponse(
        request, "index.html",
        {"brief": brief, "inbox": inbox, "prs": github.open_prs(), "dormant_days": dormant_days,
         "px_enabled": bool(px) or proxmox.enabled(), "hide_stopped": hide, "guests": guest_rows, "linked": linked,
         "sort": sort, "groups": groups, "focus": focus, "recent": recent, "status": status, "board": board,
         "board_projects": sorted({t["pname"] for col in board.values() for t in col}),
         "today": today_label(),
         "open_total": sum(len(g["active"]) + len(g["dormant"]) for g in groups.values())},
    )


@app.get("/p/{slug}", response_class=HTMLResponse)
def project_page(request: Request, slug: str):
    with closing(db()) as con:
        p = project_or_404(con, slug)
        todos = con.execute(
            "SELECT * FROM todos WHERE project=? ORDER BY done, prio, id", (slug,)
        ).fetchall()
        log = con.execute(
            "SELECT * FROM activity WHERE project=? ORDER BY id DESC LIMIT 20", (slug,)
        ).fetchall()
        notes = con.execute(
            "SELECT * FROM notes WHERE project=? ORDER BY pinned DESC, id DESC", (slug,)
        ).fetchall()
        docs = con.execute("SELECT * FROM docs WHERE project=? ORDER BY title", (slug,)).fetchall()
    gh = github.repo_detail(p["repo"]) if p["repo"] else None
    guest = proxmox.by_vmid().get(p["vmid"]) if p["vmid"] and proxmox.enabled() else None
    return templates.TemplateResponse(
        request, "project.html",
        {"p": p, "todos": todos, "log": log, "gh": gh, "notes": notes, "docs": docs, "guest": guest}
    )


@app.post("/p/{slug}/docs")
def web_doc_add(slug: str, title: str = Form(...), body: str = Form("")):
    with closing(db()) as con:
        project_or_404(con, slug)
        cur = con.execute("INSERT INTO docs(project,title,body,created,updated) VALUES(?,?,?,?,?)",
                          (slug, title.strip(), body, now(), now()))
        con.commit()
    return RedirectResponse(f"/p/{slug}#doc-{cur.lastrowid}", status_code=303)


@app.post("/d/{did}/save")
def web_doc_save(did: int, title: str = Form(...), body: str = Form("")):
    with closing(db()) as con:
        d = con.execute("SELECT * FROM docs WHERE id=?", (did,)).fetchone()
        if not d:
            raise HTTPException(404)
        con.execute("UPDATE docs SET title=?, body=?, updated=? WHERE id=?", (title.strip(), body, now(), did))
        con.commit()
    return RedirectResponse(f"/p/{d['project']}#doc-{did}", status_code=303)


@app.post("/d/{did}/delete")
def web_doc_delete(did: int):
    with closing(db()) as con:
        d = con.execute("SELECT * FROM docs WHERE id=?", (did,)).fetchone()
        if not d:
            raise HTTPException(404)
        con.execute("DELETE FROM docs WHERE id=?", (did,))
        con.commit()
    return RedirectResponse(f"/p/{d['project']}", status_code=303)


@app.post("/p/{slug}/notes")
def web_note_add(slug: str, text: str = Form(...), pinned: str = Form("")):
    with closing(db()) as con:
        project_or_404(con, slug)
        con.execute("INSERT INTO notes(project,text,author,pinned,created) VALUES(?,?,'user',?,?)",
                    (slug, text.strip(), 1 if pinned else 0, now()))
        con.commit()
    return RedirectResponse(f"/p/{slug}", status_code=303)


@app.post("/n/{nid}/pin")
def web_note_pin(nid: int):
    with closing(db()) as con:
        n = con.execute("SELECT * FROM notes WHERE id=?", (nid,)).fetchone()
        if not n:
            raise HTTPException(404)
        con.execute("UPDATE notes SET pinned=? WHERE id=?", (0 if n["pinned"] else 1, nid))
        con.commit()
    return RedirectResponse(f"/p/{n['project']}", status_code=303)


@app.post("/n/{nid}/delete")
def web_note_delete(nid: int):
    with closing(db()) as con:
        n = con.execute("SELECT * FROM notes WHERE id=?", (nid,)).fetchone()
        if not n:
            raise HTTPException(404)
        con.execute("DELETE FROM notes WHERE id=?", (nid,))
        con.commit()
    return RedirectResponse(f"/p/{n['project']}", status_code=303)


def search_all(con, q):
    like = f"%{q}%"
    return {
        "notes": con.execute(
            "SELECT n.*, p.name AS pname FROM notes n JOIN projects p ON p.slug=n.project "
            "WHERE n.text LIKE ? ORDER BY n.id DESC LIMIT 50", (like,)).fetchall(),
        "docs": con.execute(
            "SELECT d.*, p.name AS pname FROM docs d JOIN projects p ON p.slug=d.project "
            "WHERE d.title LIKE ? OR d.body LIKE ? ORDER BY d.title LIMIT 50", (like, like)).fetchall(),
        "todos": con.execute(
            "SELECT t.*, p.name AS pname FROM todos t JOIN projects p ON p.slug=t.project "
            "WHERE t.text LIKE ? ORDER BY t.done, t.id DESC LIMIT 50", (like,)).fetchall(),
        "projects": con.execute(
            "SELECT * FROM projects WHERE name LIKE ? OR summary LIKE ? OR slug LIKE ? ORDER BY name",
            (like, like, like)).fetchall(),
    }


@app.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = ""):
    q = q.strip()
    with closing(db()) as con:
        res = search_all(con, q) if q else {"notes": [], "docs": [], "todos": [], "projects": []}
    return templates.TemplateResponse(request, "search.html", {"q": q, "res": res})


@app.post("/p/{slug}/add")
def web_add(slug: str, text: str = Form(...), prio: int = Form(2), kind: str = Form("todo")):
    with closing(db()) as con:
        project_or_404(con, slug)
        con.execute(
            "INSERT INTO todos(project,text,kind,prio,created) VALUES(?,?,?,?,?)",
            (slug, text.strip(), kind, prio, now()),
        )
        con.commit()
    return RedirectResponse(f"/p/{slug}", status_code=303)


@app.post("/t/{tid}/toggle")
def web_toggle(tid: int, next: str = Form("")):
    with closing(db()) as con:
        t = con.execute("SELECT * FROM todos WHERE id=?", (tid,)).fetchone()
        if not t:
            raise HTTPException(404)
        done = 0 if t["done"] else 1
        con.execute("UPDATE todos SET done=?, done_at=? WHERE id=?",
                    (done, now() if done else None, tid))
        if done:
            con.execute("INSERT INTO activity(project,text,ts) VALUES(?,?,?)",
                        (t["project"], f"{tr('log.done')} {t['text']}", now()))
        con.commit()
    return RedirectResponse(safe_next(next, f"/p/{t['project']}"), status_code=303)


@app.post("/t/{tid}/seen")
def web_seen(tid: int, next: str = Form("/")):
    with closing(db()) as con:
        con.execute("UPDATE todos SET seen=1 WHERE id=?", (tid,))
        con.commit()
    return RedirectResponse(safe_next(next), status_code=303)


@app.post("/t/{tid}/finished")
def web_finished(tid: int, next: str = Form("/")):
    with closing(db()) as con:
        t = con.execute("SELECT * FROM todos WHERE id=?", (tid,)).fetchone()
        if not t:
            raise HTTPException(404)
        con.execute("UPDATE todos SET seen=1, done=1, done_at=? WHERE id=?", (now(), tid))
        con.execute("INSERT INTO activity(project,text,ts) VALUES(?,?,?)",
                    (t["project"], f"{tr('log.done')} {t['text']}", now()))
        con.commit()
    return RedirectResponse(safe_next(next), status_code=303)


@app.post("/inbox/seen-all")
def web_seen_all(next: str = Form("/")):
    with closing(db()) as con:
        con.execute("UPDATE todos SET seen=1 WHERE seen=0")
        con.commit()
    return RedirectResponse(safe_next(next), status_code=303)


@app.post("/t/{tid}/delete")
def web_delete(tid: int, next: str = Form("/")):
    with closing(db()) as con:
        con.execute("DELETE FROM todos WHERE id=?", (tid,))
        con.commit()
    return RedirectResponse(safe_next(next), status_code=303)


@app.post("/t/{tid}/prio")
def web_prio(tid: int, prio: int = Form(...), next: str = Form("")):
    if prio not in (1, 2, 3):
        raise HTTPException(400)
    with closing(db()) as con:
        con.execute("UPDATE todos SET prio=? WHERE id=?", (prio, tid))
        con.commit()
    return RedirectResponse(safe_next(next), status_code=303) if next else {"ok": True}


@app.post("/p/{slug}/status")
def web_status(slug: str, status: str = Form(...)):
    if status not in ("aktiv", "pause", "archiv"):
        raise HTTPException(400)
    with closing(db()) as con:
        project_or_404(con, slug)
        con.execute("UPDATE projects SET status=? WHERE slug=?", (status, slug))
        con.commit()
    return RedirectResponse(f"/p/{slug}", status_code=303)


@app.post("/p/{slug}/live")
def web_live(slug: str, live: str = Form(""), next: str = Form("")):
    with closing(db()) as con:
        project_or_404(con, slug)
        con.execute("UPDATE projects SET live=? WHERE slug=?", (1 if live else 0, slug))
        con.commit()
    return RedirectResponse(safe_next(next, f"/p/{slug}"), status_code=303)


@app.get("/design/{name}")
def set_design(name: str, next: str = "/"):
    resp = RedirectResponse(safe_next(next, "/"), status_code=303)
    resp.set_cookie("design", name if name in ("fresh", "op") else "classic", max_age=60 * 60 * 24 * 365, samesite="lax")
    return resp


@app.get("/briefing", response_class=HTMLResponse)
def briefing_page(request: Request):
    with closing(db()) as con:
        text = digest.build_digest(con)
        projects = digest.briefing_projects(con)
    return templates.TemplateResponse(request, "briefing.html", {"text": text, "projects": projects})


@app.post("/p/{slug}/log")
def web_log(slug: str, text: str = Form(...)):
    with closing(db()) as con:
        project_or_404(con, slug)
        con.execute("INSERT INTO activity(project,text,ts) VALUES(?,?,?)", (slug, text.strip(), now()))
        con.commit()
    return RedirectResponse(f"/p/{slug}", status_code=303)


# ---------- API (für Claude / Skill) ----------

class TodoIn(BaseModel):
    text: str
    prio: int = 2
    kind: str = "todo"
    short: str = ""
    check: str = ""


class LogIn(BaseModel):
    text: str


class ProjectIn(BaseModel):
    slug: str
    name: str
    status: str = "aktiv"
    area: str = ""
    deploy: str = ""
    stack: str = ""
    summary: str = ""
    vault_note: str = ""
    repo: str = ""
    wiki: str = ""
    vmid: int = 0


@app.get("/api/overview", response_class=PlainTextResponse)
def api_overview():
    with closing(db()) as con:
        rows = con.execute(
            "SELECT p.slug, p.name, p.status, p.deploy, "
            "(SELECT COUNT(*) FROM todos t WHERE t.project=p.slug AND t.done=0 AND t.kind='todo') AS n, "
            "(SELECT COUNT(*) FROM todos t WHERE t.project=p.slug AND t.done=0 AND t.kind='todo' AND t.prio=1) AS n1 "
            "FROM projects p ORDER BY p.status, p.sort, p.name"
        ).fetchall()
    return "\n".join(
        f"{r['slug']}\t{r['status']}\t{r['n']} open ({r['n1']} P1)\t{r['name']}\t{r['deploy']}" for r in rows
    )


@app.get("/api/projects/{slug}", response_class=PlainTextResponse)
def api_brief(slug: str):
    with closing(db()) as con:
        return brief(con, slug)


@app.put("/api/projects")
def api_upsert_project(p: ProjectIn):
    with closing(db()) as con:
        con.execute(
            "INSERT INTO projects(slug,name,status,area,deploy,stack,summary,vault_note,repo,wiki,vmid) "
            "VALUES(:slug,:name,:status,:area,:deploy,:stack,:summary,:vault_note,:repo,:wiki,:vmid) "
            "ON CONFLICT(slug) DO UPDATE SET name=:name,status=:status,area=:area,deploy=:deploy,stack=:stack,"
            "summary=:summary,vault_note=:vault_note,repo=:repo,wiki=:wiki,vmid=:vmid",
            p.model_dump(),
        )
        con.commit()
    return {"ok": True}


class ProjectPatch(BaseModel):
    name: str | None = None
    status: str | None = None
    area: str | None = None
    deploy: str | None = None
    stack: str | None = None
    summary: str | None = None
    vault_note: str | None = None
    repo: str | None = None
    wiki: str | None = None
    vmid: int | None = None
    live: int | None = None


@app.patch("/api/projects/{slug}")
def api_patch_project(slug: str, p: ProjectPatch):
    fields = p.model_dump(exclude_none=True)
    with closing(db()) as con:
        project_or_404(con, slug)
        if fields:
            con.execute(f"UPDATE projects SET {','.join(f'{k}=?' for k in fields)} WHERE slug=?",
                        [*fields.values(), slug])
            con.commit()
    return {"ok": True}


class DocIn(BaseModel):
    title: str
    body: str = ""
    source: str = ""


@app.post("/api/projects/{slug}/docs")
def api_doc_add(slug: str, d: DocIn):
    with closing(db()) as con:
        project_or_404(con, slug)
        cur = con.execute("INSERT INTO docs(project,title,body,source,created,updated) VALUES(?,?,?,?,?,?)",
                          (slug, d.title.strip(), d.body, d.source, now(), now()))
        con.commit()
    return {"id": cur.lastrowid}


@app.get("/api/docs/{did}", response_class=PlainTextResponse)
def api_doc_get(did: int):
    with closing(db()) as con:
        d = con.execute("SELECT * FROM docs WHERE id=?", (did,)).fetchone()
    if not d:
        raise HTTPException(404)
    return f"# {d['title']}\n\n{d['body']}"


@app.put("/api/docs/{did}")
def api_doc_put(did: int, d: DocIn):
    with closing(db()) as con:
        if not con.execute("SELECT 1 FROM docs WHERE id=?", (did,)).fetchone():
            raise HTTPException(404)
        con.execute("UPDATE docs SET title=?, body=?, updated=? WHERE id=?", (d.title.strip(), d.body, now(), did))
        con.commit()
    return {"ok": True}


class NoteIn(BaseModel):
    text: str
    pinned: bool = False


@app.post("/api/projects/{slug}/notes")
def api_note_add(slug: str, n: NoteIn):
    with closing(db()) as con:
        project_or_404(con, slug)
        cur = con.execute("INSERT INTO notes(project,text,author,pinned,created) VALUES(?,?,'agent',?,?)",
                          (slug, n.text.strip(), int(n.pinned), now()))
        con.commit()
    return {"id": cur.lastrowid}


@app.put("/api/notes/{nid}")
def api_note_put(nid: int, n: NoteIn):
    with closing(db()) as con:
        if not con.execute("SELECT 1 FROM notes WHERE id=?", (nid,)).fetchone():
            raise HTTPException(404)
        con.execute("UPDATE notes SET text=?, pinned=? WHERE id=?", (n.text.strip(), int(n.pinned), nid))
        con.commit()
    return {"ok": True}


@app.get("/api/search", response_class=PlainTextResponse)
def api_search(q: str):
    with closing(db()) as con:
        res = search_all(con, q.strip())
    lines = [f"note #{n['id']} [{n['project']}] {n['created']}: {n['text'][:200]}" for n in res["notes"]]
    lines += [f"doc #{d['id']} [{d['project']}] {d['title']}" for d in res["docs"]]
    lines += [f"todo #{t['id']} [{t['project']}] {'done' if t['done'] else 'open'}: {t['text'][:200]}"
              for t in res["todos"]]
    lines += [f"project {p['slug']}: {p['name']}" for p in res["projects"]]
    return "\n".join(lines) or "no results"


class TodoPatch(BaseModel):
    project: str | None = None
    text: str | None = None
    short: str | None = None
    check: str | None = None
    prio: int | None = None
    kind: str | None = None


@app.patch("/api/todos/{tid}")
def api_patch_todo(tid: int, p: TodoPatch):
    fields = p.model_dump(exclude_none=True)
    if "check" in fields:
        fields["check_spec"] = fields.pop("check")
    with closing(db()) as con:
        if not con.execute("SELECT 1 FROM todos WHERE id=?", (tid,)).fetchone():
            raise HTTPException(404)
        if "project" in fields:
            project_or_404(con, fields["project"])
        if fields:
            con.execute(f"UPDATE todos SET {','.join(f'{k}=?' for k in fields)} WHERE id=?", [*fields.values(), tid])
            con.commit()
    return {"ok": True}


@app.post("/api/projects/{slug}/todos")
def api_add(slug: str, t: TodoIn):
    with closing(db()) as con:
        project_or_404(con, slug)
        cur = con.execute(
            "INSERT INTO todos(project,text,kind,prio,created,source,seen,short,check_spec) VALUES(?,?,?,?,?,'agent',0,?,?)",
            (slug, t.text, t.kind, t.prio, now(), t.short.strip(), t.check.strip()),
        )
        con.commit()
    return {"id": cur.lastrowid}


@app.post("/api/todos/{tid}/done")
def api_done(tid: int):
    with closing(db()) as con:
        t = con.execute("SELECT * FROM todos WHERE id=?", (tid,)).fetchone()
        if not t:
            raise HTTPException(404)
        con.execute("UPDATE todos SET done=1, done_at=? WHERE id=?", (now(), tid))
        con.execute("INSERT INTO activity(project,text,ts) VALUES(?,?,?)",
                    (t["project"], f"{tr('log.done')} {t['text']}", now()))
        con.commit()
    return {"ok": True}


@app.post("/api/projects/{slug}/log")
def api_log(slug: str, e: LogIn):
    with closing(db()) as con:
        project_or_404(con, slug)
        con.execute("INSERT INTO activity(project,text,ts) VALUES(?,?,?)", (slug, e.text, now()))
        con.commit()
    return {"ok": True}


@app.get("/export/notes.md", response_class=PlainTextResponse)
def export_notes_md():
    with closing(db()) as con:
        rows = con.execute(
            "SELECT n.*, p.name AS pname FROM notes n JOIN projects p ON p.slug=n.project "
            "ORDER BY p.name, n.pinned DESC, n.id DESC").fetchall()
    out, current = ["# Notes (generated)\n"], None
    for n in rows:
        if n["pname"] != current:
            current = n["pname"]
            out.append(f"\n## {current}\n")
        out.append(f"### {n['created']} ({n['author']}){' [pinned]' if n['pinned'] else ''}\n\n{n['text']}\n")
    return "\n".join(out)


@app.get("/export/todo.md", response_class=PlainTextResponse)
def export_md():
    with closing(db()) as con:
        slugs = [r["slug"] for r in con.execute(
            "SELECT slug FROM projects WHERE status='aktiv' ORDER BY sort, name")]
        parts = [f"# TODO list (generated)\n\n**Updated:** {now()[:10]}\n"]
        parts += [brief(con, s) for s in slugs]
    return "\n\n---\n\n".join(parts)
