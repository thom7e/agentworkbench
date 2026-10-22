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
2. **While working**
   - Tick off a finished task: `curl -s -X POST -H "$H" "$AWB_URL/api/todos/<id>/done"`
   - Add a task (it lands in the user's inbox):
     ```bash
     curl -s -X POST -H "$H" -H "Content-Type: application/json; charset=utf-8" \
       --data-binary '{"text":"...","prio":2}' "$AWB_URL/api/projects/<slug>/todos"
     ```
     Use `prio` 1 only for deadlines or risks. Ideas: add `"kind":"idee"`.
   - Save lasting knowledge as a **note** (a decision and its reason, a pitfall, how to reach something). Pin only what matters:
     ```bash
     curl -s -X POST -H "$H" -H "Content-Type: application/json; charset=utf-8" \
       --data-binary '{"text":"...","pinned":false}' "$AWB_URL/api/projects/<slug>/notes"
     ```
   - Search notes, documents, tasks and projects: `curl -s -H "$H" "$AWB_URL/api/search?q=<term>"`
   - Documents (longer Markdown pages): the briefing lists them. Read with `GET /api/docs/<id>`, change with `PUT /api/docs/<id>` and `{"title":"...","body":"..."}`, create with `POST /api/projects/<slug>/docs`. Read before changing and change only what is needed.
   - Move a task to another project or change its priority: `PATCH /api/todos/<id>` with `{"project":"<slug>","prio":2}`
   - Change project fields without touching the rest: `PATCH /api/projects/<slug>`
3. **End:** one log entry, a sentence on what was done, with a commit hash if there is one.
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

- Tick off only tasks that are really finished and verified.
- No duplicates: check the briefing before adding.
- No passwords, tokens or other credentials in any text.
- Unknown project: ask the user, do not guess. A new project is created with `PUT /api/projects` (`slug`, `name`, optionally `area`, `deploy`, `stack`, `summary`, `repo`).
- Answer `401` means the token is missing or revoked: tell the user.
- Send JSON as UTF-8 (`--data-binary` with the charset header).
