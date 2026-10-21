# AgentWorkbench

A small self-hosted dashboard that gives you and your AI agents one shared view of every project: open tasks, ideas, a priority board, recent activity and live GitHub data. Open it in the morning, see what matters, and let agents such as Claude Code keep it up to date while they work.

- **Priority board** across all projects. Drag a card to change its priority (on phones: tap 1, 2 or 3).
- **Today list** with every urgent task, check off in place.
- **Inbox** for tasks that agents created since you last looked, plus open pull requests.
- **Project pages** with tasks, ideas, activity log, branches, latest commits and README excerpt from GitHub.
- **Notes as project memory**: timestamped notes per project from you or an agent, pinnable. Agents get pinned and recent notes in their briefing. Full-text search across notes, tasks and projects.
- **Groups** you define yourself (hosting target, client, team...), sortable by recent activity or open tasks, with a collapsed "dormant" group for quiet projects.
- **Admin area**: settings, projects, API tokens, JSON backup and Markdown import.
- **Agent API** with revocable tokens. Agents read a project brief and write tasks and log entries.
- **Installable on a phone** (iOS and Android): add it to the home screen, it opens full screen.
- German and English UI.

One FastAPI process, one SQLite file, no build step.

## Quick start

```bash
git clone https://github.com/thom7e/agentworkbench.git
cd agentworkbench
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`. The first visit asks you to choose the admin password. Then open **Admin → Settings** to set the language, your groups and your GitHub account.

## Configuration

Everything is configured in the admin area. A few values come from the environment:

| Variable | Default | Purpose |
|---|---|---|
| `AGENTWORKBENCH_DB` | `./dashboard.db` | Path of the SQLite file |
| `AGENTWORKBENCH_COOKIE_SECURE` | `0` | Set to `1` when served over HTTPS |
| `AGENTWORKBENCH_TOKEN` | empty | Optional static API token (tokens from the admin area are preferred) |
| `GITHUB_TOKEN` | empty | Fallback if no token is stored in the settings |

GitHub features (commits, branches, pull requests, last push) need a fine-grained token with read-only access to your repositories. Without it, the rest of the app works unchanged.

## Agent API

Create a token under **Admin → API access**. It is shown once and stored only as a hash.

```bash
curl -H "Authorization: Bearer $TOKEN" https://your-host/api/overview
curl -H "Authorization: Bearer $TOKEN" https://your-host/api/projects/my-project
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"text": "Add rate limiting", "prio": 1}' https://your-host/api/projects/my-project/todos
curl -X POST -H "Authorization: Bearer $TOKEN" https://your-host/api/todos/42/done
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"text": "Fixed the login redirect"}' https://your-host/api/projects/my-project/log
```

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \n     -d '{"text": "Decided: SQLite is enough, no Postgres", "pinned": true}' https://your-host/api/projects/my-project/notes
curl -H "Authorization: Bearer $TOKEN" "https://your-host/api/search?q=sqlite"
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \n     -d '{"status": "pause"}' https://your-host/api/projects/my-project
```

Tasks created through the API land in the inbox until you mark them as seen. `GET /export/notes.md` returns all notes as Markdown.

## Install on a phone

Open the site in Safari (iPhone) or Chrome (Android), then use **Share → Add to Home Screen**. The app opens without browser chrome and keeps you signed in for 30 days.

Serve it over HTTPS if you reach it from outside your network, and set `AGENTWORKBENCH_COOKIE_SECURE=1`.

## Security notes

- Everything except the login page requires the admin password. The API requires a token.
- Passwords are hashed with scrypt, API tokens with SHA-256, sessions are signed cookies.
- Login attempts are rate limited per IP, cross-origin form posts are rejected.
- There is a single admin account. Put the app behind HTTPS and, if it is reachable from the internet, an access proxy of your choice.

## Tests

```bash
pytest
```

## License

MIT
