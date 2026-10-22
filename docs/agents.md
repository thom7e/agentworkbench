# Working with agents

AgentWorkbench is built so that an AI agent can pick up a project the way a colleague would: read what is open and what was decided, do the work, and leave a trace.

## The idea

1. **Briefing.** Before the agent starts on a project it fetches one Markdown text with everything it needs: where the project runs, open tasks with priority, ideas, pinned notes, the latest notes, the document list, recently finished work and the last log entries.
2. **Work.** While it works the agent ticks off finished tasks, adds new tasks and ideas, and saves anything worth remembering as a note.
3. **Trace.** At the end it writes one log entry: what was done, in a sentence, ideally with a commit hash.

Nothing is written without a token, and every write by an agent is visible: new tasks land in your **inbox** until you accept, mark as done or discard them.

## Log, notes or documents?

| | Log entry | Note | Document |
|---|---|---|---|
| Answers | What was done? | What should I still know later? | How does it work? |
| Length | One sentence | A few lines | A page or more |
| Examples | "Fixed the login redirect (abc123)" | "Decided against Postgres, SQLite is enough. Reason: single writer" | Runbook, checklist, specification |
| In the briefing | Last 8 | Pinned and the latest 5 | Title list only, read on demand |

Rule of thumb for agents: if it will still matter after the log has scrolled away, it is a note.

## Tokens

Create one token per agent under **Admin → API access**. A token is shown once and stored only as a hash. Revoke it there at any time. Tokens give full API access, see [Security](security.md).

## Claude Code

A ready-made skill and a snippet for your `CLAUDE.md` are in [`examples/claude-code`](../examples/claude-code).

1. Store the address and the token in a file only you can read, for example `~/.claude/agentworkbench.env`:

   ```bash
   AWB_URL=https://workbench.example.com
   AWB_TOKEN=wb_...
   ```

2. Copy `examples/claude-code/SKILL.md` to `~/.claude/skills/agentworkbench/SKILL.md`.
3. Add the snippet from `examples/claude-code/CLAUDE.md.snippet.md` to your global `~/.claude/CLAUDE.md`, so every session knows the dashboard exists.

From then on, asking "what is open in project X?" or starting work on a project makes Claude Code fetch the briefing and keep the dashboard up to date.

## Any other agent or script

The API is plain HTTP with JSON bodies and a Bearer token, so it works from any tool. See the [API reference](api.md). A minimal loop:

```bash
H="Authorization: Bearer $TOKEN"
curl -s -H "$H" "$URL/api/overview"                       # which projects exist
curl -s -H "$H" "$URL/api/projects/website"               # briefing
curl -s -X POST -H "$H" "$URL/api/todos/42/done"          # tick off
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
     -d '{"text":"Added rate limiting (abc123)"}' "$URL/api/projects/website/log"
```

Send JSON as UTF-8 (`Content-Type: application/json; charset=utf-8`), especially on Windows shells.

## Tips

- Keep the **briefing short and current**: archive projects you no longer work on, they disappear from the board.
- Give agents **one project at a time**. The slug identifies it, `GET /api/overview` lists all slugs.
- Ask agents to **read a document before changing it** and to change only what is needed.
- Do not let agents write secrets into notes or documents. Keep credentials in a password manager.
