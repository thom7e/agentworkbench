# API reference

English · [Deutsch](de/api.md)

Base URL: the address of your instance, for example `https://workbench.example.com`.

## Authentication

Send a token in the `Authorization` header:

```
Authorization: Bearer wb_...
```

Create tokens under **Admin → API access**. A signed-in browser session also works for the pages. Without a valid token the API answers `401`.

Request bodies are JSON (`Content-Type: application/json`, UTF-8). Unknown fields are ignored. Unknown projects, tasks, notes or documents answer `404`.

## Values

| Field | Values |
|---|---|
| `status` | `aktiv` (active), `pause` (paused), `archiv` (archived) |
| `kind` | `todo` (task), `idee` (idea) |
| `prio` | `1` urgent, `2` normal, `3` someday |
| `live` | `1` live or at the customer, `0` not |

## Overview and briefing

### `GET /api/overview`

Plain text, one project per line, tab separated: `slug`, `status`, `N open (M P1)`, `name`, `hosting`.

```bash
curl -H "Authorization: Bearer $TOKEN" $URL/api/overview
```

### `GET /api/projects/{slug}`

The briefing as Markdown:

```
# Project name (slug) — aktiv
Deploy: ...            hosting, stack, repo, linked notes, wiki (only if set)
Runs on: LXC 137 ...   only with the Proxmox integration
Summary text

## Documents (read with GET /api/docs/<id>)
## Pinned notes
## Recent notes        latest 5 unpinned notes
## Open                open tasks as "- [ ] #id (P1) text"
## Ideas
## Recently done       last 5
## Log                 last 8 entries
```

Task ids in the briefing are the ids used by the endpoints below.

## Projects

### `PUT /api/projects`

Create or fully replace a project. Fields not sent are reset to their defaults, except `live`, which this call never changes (use `PATCH`).

```json
{"slug": "website", "name": "Website relaunch", "status": "aktiv", "area": "Customer sites",
 "deploy": "VPS", "stack": "Django", "summary": "Relaunch for the bakery",
 "vault_note": "https://example.com/spec", "repo": "me/website", "wiki": "", "vmid": 0}
```

`slug` and `name` are required. `area` should be one of the groups from the settings. `vault_note` (a historical name) takes one web address per line, shown as links on the project page.

### `PATCH /api/projects/{slug}`

Change only the fields you send. Accepts `name`, `status`, `area`, `deploy`, `stack`, `summary`, `vault_note`, `repo`, `wiki`, `vmid` and `live`.

```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"status": "pause"}' $URL/api/projects/website
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"live": 1}' $URL/api/projects/website
```

## Tasks

### `POST /api/projects/{slug}/todos`

```json
{"text": "Add rate limiting to the login", "short": "Limit login attempts", "prio": 1, "kind": "todo", "check": ""}
```

| Field | Meaning |
|---|---|
| `text` | The full description, details allowed. Required |
| `short` | One-line, plain-language title used in the briefing. Without it the text is shortened automatically |
| `prio` | Defaults to `2` |
| `kind` | Defaults to `todo` |
| `check` | Optional machine check as a JSON **string**, see [Briefing and checks](briefing-and-checks.md#checks). When it passes, the task is ticked off automatically |

Returns `{"id": 42}`. Tasks created through the API are marked as coming from an agent and appear in the **inbox** until a person accepts, finishes or discards them.

### `PATCH /api/todos/{id}`

Change `project` (move to another project), `text`, `short`, `check`, `prio` or `kind`.

```json
{"project": "other-project", "prio": 1}
```

### `POST /api/todos/{id}/done`

Mark a task as done and write an activity entry.

## Activity log

### `POST /api/projects/{slug}/log`

```json
{"text": "Fixed the login redirect (abc123)"}
```

## Notes

### `POST /api/projects/{slug}/notes`

```json
{"text": "Decided: SQLite is enough, no Postgres. Reason: single writer.", "pinned": true}
```

Returns `{"id": 7}`. The note is marked as written by an agent. Pinned notes are always part of the briefing.

### `PUT /api/notes/{id}`

Replace text and pin state of a note: `{"text": "...", "pinned": false}`. Useful to keep a synchronised copy of an external source up to date instead of creating duplicates.

## Documents

### `POST /api/projects/{slug}/docs`

```json
{"title": "Runbook", "body": "# Runbook\n\n1. ...", "source": ""}
```

Returns `{"id": 3}`. `body` is Markdown.

### `GET /api/docs/{id}`

Returns the document as Markdown text, starting with its title as heading.

### `PUT /api/docs/{id}`

Replace title and body: `{"title": "...", "body": "..."}`. Read the document first and send back the full text.

## Search

### `GET /api/search?q=term`

Plain text, one hit per line: `note #7 [slug] date: text`, `doc #3 [slug] title`, `todo #42 [slug] open|done: text`, `project slug: name`. Answers `no results` if nothing matches. The search is a case-insensitive substring match.

## Exports

| Endpoint | Returns |
|---|---|
| `GET /export/todo.md` | The briefings of all active projects, concatenated, as Markdown |
| `GET /export/notes.md` | All notes grouped by project |

## Health check

`GET /healthz` returns `ok` and needs no authentication.

## Browser-only endpoints

These are used by the web interface and need a signed-in browser session, not a token. They are listed for completeness.

| Endpoint | Purpose |
|---|---|
| `GET /briefing` | The briefing page |
| `GET /push/key`, `POST /push/subscribe`, `POST /push/test` | Register a device for push notifications and send a test |
| `GET /passkey/register/options`, `POST /passkey/register/verify`, `POST /passkey/{id}/delete` | Add and remove passkeys |
| `GET /passkey/login/options`, `POST /passkey/login/verify` | Passkey sign-in (public) |
| `GET /sw.js` | The service worker (public) |
