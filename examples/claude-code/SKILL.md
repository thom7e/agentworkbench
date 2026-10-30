---
name: agentworkbench
description: Read and update the AgentWorkbench project dashboard. Use at the start of work on a project (fetch the briefing), while working (tick off tasks, add tasks, ideas and notes) and at the end (write a log entry). Also for questions like "what is open", "which tasks", "status of <project>".
---

# AgentWorkbench

The dashboard is the source of truth for project status, tasks, ideas and notes. Credentials are in `~/.claude/agentworkbench.env` (`AWB_URL`, `AWB_TOKEN`). Never print the token and never write it into files or entries.

Start every command with:

```bash
. ~/.claude/agentworkbench.env; H="Authorization: Bearer $AWB_TOKEN"
```

## Workflow

1. **Start:** find the project slug, then read the briefing.
   ```bash
   curl -s -H "$H" "$AWB_URL/api/overview"
   curl -s -H "$H" "$AWB_URL/api/projects/<slug>"
   ```
   The briefing lists open tasks with id and priority (P1 urgent, P2 normal, P3 someday), ideas, pinned and recent notes, documents, recently finished work and the latest log entries.
   **Check at the start:** compare every open task with the real state (read-only: repository, service, file, log). If a task is provably done already, tick it off at once and name the evidence in the log ("checked: ...").
2. **While working**
   - **Tick off at once** when a task is finished and verified, not only at the end. Also tasks that were finished on the side: `curl -s -X POST -H "$H" "$AWB_URL/api/todos/<id>/done"`
   - Add a task (it lands in the user's inbox):
     ```bash
     curl -s -X POST -H "$H" -H "Content-Type: application/json; charset=utf-8" \
       --data-binary '{"text":"...","short":"...","prio":2}' "$AWB_URL/api/projects/<slug>/todos"
     ```
     `short` is a one-line title in plain language without paths, commands or jargon, the way you would tell a non-technical person. The morning briefing shows it; `text` may hold the details. Use `prio` 1 only for deadlines or risks. Ideas: add `"kind":"idee"`.
     **Machine check (optional `check`):** if completion can be proven by a network probe (page returns 200, text on the page, redirect, DNS, open port), pass `check` as a JSON string, for example `"check":"{\"type\":\"http\",\"url\":\"https://example.com/robots.txt\",\"contains\":\"Sitemap:\"}"`. Types: `http` (`url`, `status`, `contains`, `not_contains`, `location_contains`), `dns` (`host`, `ip`), `port` (`host`, `port`); a list means all must pass. A daily run ticks the task off with a log entry. Only set a check that proves the whole task. Add one later with `PATCH /api/todos/<id>` and `{"check":"..."}`.
   - Save lasting knowledge as a **note** (a decision and its reason, a pitfall, how to reach something). Pin only what matters:
     ```bash
     curl -s -X POST -H "$H" -H "Content-Type: application/json; charset=utf-8" \
       --data-binary '{"text":"...","pinned":false}' "$AWB_URL/api/projects/<slug>/notes"
     ```
   - Search notes, documents, tasks and projects: `curl -s -H "$H" "$AWB_URL/api/search?q=<term>"`
   - Documents (longer Markdown pages): the briefing lists them. Read with `GET /api/docs/<id>`, change with `PUT /api/docs/<id>` and `{"title":"...","body":"..."}`, create with `POST /api/projects/<slug>/docs`. Read before changing and change only what is needed.
   - Move a task to another project or change its priority: `PATCH /api/todos/<id>` with `{"project":"<slug>","prio":2}`
   - Change project fields without touching the rest: `PATCH /api/projects/<slug>`. `live` (`1` or `0`) marks a project as live or at the customer; those projects get their own section in the morning briefing, all others appear in one line.
3. **End, closing check (never skip):**
   1. Fetch the briefing again and go through all open tasks of the project, including those of other agents.
   2. Tick off every task that was finished in this session or whose completion is proven on the system.
   3. Partly done: do not tick off. Shorten the text with `PATCH /api/todos/<id>` to the remainder, or create a new task for the rest and tick off the old one.
   4. Unsure: do not tick off, tell the user in your answer ("possibly done: #12, please confirm").
   5. One log entry, a sentence on what was done, with a commit hash if there is one. Add follow-up work as a new task.
   ```bash
   curl -s -X POST -H "$H" -H "Content-Type: application/json; charset=utf-8" \
     --data-binary '{"text":"..."}' "$AWB_URL/api/projects/<slug>/log"
   ```

## Log or note?

- **Log:** what was done, one sentence, in time order.
- **Note:** what someone needs to know later even when the log has scrolled away. Check the briefing first to avoid duplicates.

## Work without a repository

Not every project has a repository. For servers, containers, networks or backups pick the project of that service, or a general infrastructure project. Record every change as a log entry: what changed, where, and which backup was taken first. Open follow-up work becomes a task.

## Rules

- **Ticking off is mandatory:** a finished but still open task is a mistake. So is ticking off without proof. Finished means verified (test green, service running, file present, commit there), not just attempted.
- Name the evidence briefly, in the log entry or in your answer ("checked: limit set in the running unit").
- No duplicates: check the briefing before adding.
- No passwords, tokens or other credentials in any text.
- Unknown project: ask the user, do not guess. A new project is created with `PUT /api/projects` (`slug`, `name`, optionally `area`, `deploy`, `stack`, `summary`, `repo`).
- Answer `401` means the token is missing or revoked: tell the user.
- Send JSON as UTF-8 (`--data-binary` with the charset header).
