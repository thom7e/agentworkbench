# Briefing and checks

English · [Deutsch](de/briefing-and-checks.md)

Three small ideas keep the dashboard short and current: a **live flag** on projects, a **short title** on tasks, and **checks** that close tasks by themselves. Together they power the morning briefing.

## The live flag

A project is **live** when it runs in production or is with a customer. Everything else (ideas, experiments, internal tools in development) is not.

- Set it with the **live** checkbox on the project page, in the list under **Briefing → Projects in the briefing**, or with the API (`PATCH /api/projects/{slug}` with `{"live": 1}`).
- Live projects appear in the **side menu** (desktop) with a lamp that is red when a task with priority 1 is open, and in the **Urgent** part of the briefing.
- Projects that are not live appear in the briefing only as one line with a task count.

## Short titles

Every task can carry a **short title**: one line in plain language, without paths, commands or jargon, the way you would say it to someone who is not technical. The text can still hold all the details.

- Agents send it as `short` when they create a task (see [API](api.md#tasks)). The Claude Code skill in `examples/claude-code` asks for it.
- Without a short title the dashboard shortens the text automatically (first sentence, markup and code removed). That works, but a hand-written title reads better.

## The morning briefing

`digest.py` builds one short text and sends it as a push notification. The same text is shown on the page `/briefing`.

What is in it:

1. **Urgent: live or at the customer.** Every live project with open tasks of priority 1 or 2: project name in bold, up to three short titles, `(+N more)` for the rest. Projects with the most urgent tasks come first.
2. **Everything else open.** One line: project names with their task counts, the biggest first (up to 20).
3. **Open for a long time.** Tasks that have been open for more than 30 days, by project.
4. **Pull requests.** Open pull requests on your GitHub account, if GitHub is connected.

Left out on purpose: paused and archived projects, tasks with priority 3, ideas and everything already done. The text follows the interface language (German or English) and greets you by the first name from **Admin → Settings → Your first name**.

The notification shows the first lines. Tapping it opens `/briefing` with the full text. Below it you find the project list with a checkbox per project: that is the live flag. Changes apply immediately.

Sending it every morning is a timer on your server, see [Deployment → Morning briefing and checks](deployment.md#morning-briefing-and-checks). Notifications are explained in [Phone and desktop](phone-and-desktop.md#notifications).

## Checks

A **check** is a small machine test attached to a task. When it passes, the task is ticked off automatically, an entry is written to the project log (`Ticked off automatically (check): ...`) and you get a notification.

### Writing a check

A check is a JSON object, or a list of objects that must **all** pass:

| Type | Fields | Passes when |
|---|---|---|
| `http` | `url`, optional `status` (default 200), `contains`, `not_contains`, `location_contains` | The page answers with that status and the text conditions hold. With `location_contains` redirects are not followed and the `Location` header must contain the text |
| `dns` | `host`, `ip` | The host resolves to that address |
| `port` | `host`, `port` | A TCP connection can be opened |

Examples:

```json
{"type": "http", "url": "https://example.com/robots.txt", "contains": "Sitemap:"}
{"type": "http", "url": "http://example.com/", "status": 301, "location_contains": "https://example.com/"}
[{"type": "dns", "host": "www.example.com", "ip": "203.0.113.10"}, {"type": "port", "host": "www.example.com", "port": 443}]
```

Add a check when you create the task (field `check`, a JSON **string**) or later with `PATCH /api/todos/{id}`:

```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"check": "{\"type\":\"http\",\"url\":\"https://example.com/\",\"contains\":\"Welcome\"}"}' \
     $URL/api/todos/42
```

### Rules of thumb

- **Only prove the whole task.** If the check covers only part of it, the task would be closed too early. Combine several conditions in a list.
- A check that **cannot run** (page unreachable, invalid JSON) counts as *not passed*. It never closes a task by mistake.
- Checks run from the server that hosts the dashboard, so they only see what that server can reach. They do not log in anywhere and read at most 2 MB of a page.
- Tasks that depend on people ("ask the customer", "decide") cannot be checked. Leave them to the closing check of your agent or to you.

### Running them

`checks.py` runs all checks of open tasks once. `python checks.py --dry` only reports and changes nothing. A daily timer is described in [Deployment](deployment.md#morning-briefing-and-checks). The last result of each check is stored with the task.
