[![CI](https://github.com/thom7e/agentworkbench/actions/workflows/ci.yml/badge.svg)](https://github.com/thom7e/agentworkbench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Self-hosted](https://img.shields.io/badge/self--hosted-FastAPI%20%2B%20SQLite-informational)

English · [Deutsch](README.de.md)

```text
    ___                    __ _       __           __   __                    __
   /   | ____ ____  ____  / /| |     / /___  _____/ /__/ /_  ___  ____  _____/ /_
  / /| |/ __ `/ _ \/ __ \/ __/ | /| / / __ \/ ___/ //_/ __ \/ _ \/ __ \/ ___/ __ \
 / ___ / /_/ /  __/ / / / /_ | |/ |/ / /_/ / /  / ,< / /_/ /  __/ / / / /__/ / / /
/_/  |_\__, /\___/_/ /_/\__/ |__/|__/\____/_/  /_/|_/_.___/\___/_/ /_/\___/_/ /_/
      /____/
```

**One shared view of all your projects, for you and your AI agents.**
Agents answer project questions with about 36 to 47 % fewer tokens and fewer steps, at the same accuracy.

```text
  ┌───────────────┐  push, briefing page   ┌──────────────────────────┐  briefing, tasks   ┌──────────────┐
  │      you      │◄───────────────────────│     A G E N T            │◄──────────────────►│   AI agents  │
  │ phone · web   │                        │     W O R K B E N C H    │  notes, log        │ Claude Code  │
  │ desktop       │───── tick off, add ───►│  FastAPI + SQLite        │                    │ and friends  │
  └───────────────┘                        └─────────────┬────────────┘                    └──────────────┘
                                                         │ checks: HTTP · DNS · port
                                                         ▼ close tasks by themselves
                                           ┌──────────────────────────┐
                                           │  your sites and servers  │
                                           └──────────────────────────┘
```

What an agent gets before it starts (one short text per project):

```text
$ curl -H "Authorization: Bearer $TOKEN" https://your-host/api/projects/dental-booking

# Dental Practice Booking (dental-booking) — aktiv
Deploy: VPS
Stack: Django, PostgreSQL

## Recent notes
### #5 2026-10-30 09:15 (user)
The front desk wants to see the day list sorted by time, not by name.

## Open
- [ ] #6  (P1) Send a reminder e-mail 24 hours before the appointment
- [ ] #24 (P1) Time zone bug: appointments after 23:00 are stored one day earlier
- [ ] #7  (P2) Let patients cancel through a link in the e-mail

## Log
- 2026-10-30 16:15 Reminder e-mails drafted, waiting for the privacy text
```

Measured, not guessed: the same five project questions, once from Markdown notes and once through AgentWorkbench, same model, 25 runs per row. Method, caveats and how to reproduce: [benchmark](benchmark/README.md).

```text
  Tokens per question, lower is better

  12 projects
  Markdown files   █████████████████████████████████████    18,300
  AgentWorkbench   ████████████████████                      9,800  -47 %

  60 projects
  Markdown files   ██████████████████████████████████████   18,900
  AgentWorkbench   ████████████████████████                 12,000  -36 %
```

<details>
<summary>Full table</summary>

| Projects | Variant | Correct | Tokens per question | Steps | Cost |
|---|---|---|---|---|---|
| 12 | Markdown files | 24 / 25 | 18,300 | 3.7 | $0.0076 |
| 12 | **AgentWorkbench** | 25 / 25 | **9,800** (-47 %) | 2.8 | $0.0055 (-28 %) |
| 60 | Markdown files | 25 / 25 | 18,900 | 4.0 | $0.0121 |
| 60 | **AgentWorkbench** | 25 / 25 | **12,000** (-36 %) | 2.8 | $0.0076 (-37 %) |

The gain is largest for questions that span projects ("what is urgent everywhere?"). Looking up one note is a tie. The test data is small and the baseline files are tidy, so read it as an indication.

</details>

AgentWorkbench is a small self-hosted dashboard. You open it in the morning (or get it as a notification) and see what matters: what is live and at the customer, what is urgent, what your agents did and what changed on GitHub. Agents such as [Claude Code](https://claude.com/claude-code) read a short briefing before they start, tick off tasks and leave notes for the next time, so nothing has to be re-explained.

One FastAPI process, one SQLite file, no build step. English and German interface, installable on your phone.

<p align="center">
  <img src="docs/images/demo.gif" alt="Short demo: tick off a task, open a project, the briefing and the search" width="860">
</p>
<p align="center">
  <img src="docs/images/dashboard-light.png" alt="Home page with the side menu, urgent tasks and recent activity" width="860">
</p>
<p align="center">
  <img src="docs/images/briefing.png" alt="The briefing page" width="420">
  <img src="docs/images/mobile.png" alt="Phone: today" width="190">
  <img src="docs/images/mobile-projects.png" alt="Phone: projects" width="190">
</p>

## What it does

**Overview**
- **Today first**: every urgent task across all projects in one list, tick off in place.
- **Projects** in groups you define, with a *live* flag for what runs for customers or in production. Live projects are listed in the side menu with a lamp that turns red when something is urgent.
- **Project pages** with tabs: tasks and ideas, notes, documents, and an activity tab with the log, Git branches and latest commits.
- **Inbox** for tasks that agents created since you last looked: *Accept*, *Already done* or *Discard*. Open pull requests show up there too.
- **Priority board** (drag a card to change its priority) and **search** across notes, documents, tasks and projects.

**Briefing and automation**
- **Morning briefing** as a push notification: live projects first with one plain-language line per task, everything else in one line, a hint for tasks that stayed open for more than 30 days. Tapping it opens the briefing page where you choose which projects count as live.
- **Checks that close tasks for you**: a task can carry a small machine check (page returns 200, text present, redirect, DNS, open port). A daily run ticks it off, writes a log entry and notifies you.
- **Notes as memory**: timestamped notes from you or an agent, pinnable. Agents get the pinned and the latest notes with every briefing.

**For agents**
- A compact **briefing** per project (Markdown, short), a small **HTTP API** with revocable tokens, and a ready-made [Claude Code skill](examples/claude-code).

**Phone and desktop**
- **Phone app**: add it to the home screen. It reads offline, has a quick-add button with an offline queue, swipe to tick off, pull to refresh and web push.
- **Passkey sign-in** (Face ID, Touch ID, Windows Hello) next to the password.
- **Desktop terminal** (optional, Windows): a button on every task opens a terminal in the project folder with your AI agent and the task as its starting prompt.

**Operations**
- Optional read-only **Proxmox** integration (status and IP per project), **admin area** with settings, projects, API tokens, JSON backup and Markdown import. Light and dark theme follow your system.

## Quick start

### Docker (recommended)

```bash
git clone https://github.com/thom7e/agentworkbench.git
cd agentworkbench
docker compose up -d
```

Open <http://localhost:8000>. The first visit asks you to choose the admin password. Data lives in the `agentworkbench-data` volume.

Alternatively, after a maintainer's first successful `v*` image publication, start a fresh install without cloning or building. Replace `vX.Y.Z` with a published version tag; the workflow does not publish `latest`:

```bash
docker run -d --name agentworkbench --restart unless-stopped \
  -p 127.0.0.1:8000:8000 -v agentworkbench-data:/data \
  ghcr.io/thom7e/agentworkbench:vX.Y.Z
```

Choose one Docker method: they use the same container name and port. For existing Compose data and image availability, see [Deployment](docs/deployment.md#published-docker-image).

### Python

```bash
git clone https://github.com/thom7e/agentworkbench.git
cd agentworkbench
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Try it with demo data

```bash
AGENTWORKBENCH_DB=./demo.db python scripts/demo_seed.py
AGENTWORKBENCH_DB=./demo.db uvicorn app:app
```

Sign in with `demo-password-123`. The demo contains fictional projects, an inbox, notes and documents.

> Passkeys and push notifications need HTTPS (a real domain, or `localhost`). See [Deployment](docs/deployment.md#https-and-reverse-proxy).

## Documentation

| Guide | Contents |
|---|---|
| [Getting started](docs/getting-started.md) | First run, first project, daily workflow |
| [Configuration](docs/configuration.md) | Every setting and environment variable |
| [Briefing and checks](docs/briefing-and-checks.md) | The live flag, short titles, the morning briefing, machine checks |
| [Phone and desktop](docs/phone-and-desktop.md) | Phone app, notifications, passkeys, the desktop terminal |
| [Working with agents](docs/agents.md) | The briefing, notes vs. log, a ready-made Claude Code skill |
| [API reference](docs/api.md) | All endpoints with examples |
| [Proxmox integration](docs/proxmox.md) | Read-only token, linking projects to containers |
| [Deployment](docs/deployment.md) | Docker, systemd, HTTPS, timers, backups, updates, password reset |
| [Security](docs/security.md) | What is protected, what is not |
| [Benchmark](benchmark/README.md) | Tokens, steps and cost for agents: files vs. AgentWorkbench, method and caveats |
| [Development](docs/development.md) | Project layout, tests, translations, screenshots |

Every guide is also available in German in [`docs/de`](docs/de).

## Why agents like it

An agent needs to know what is open, what was decided and where something runs, without reading whole files. The briefing is one short Markdown text per project: open tasks with priority, pinned and recent notes, a list of documents (read on demand) and the last log entries. Tasks carry a one-line title, so the morning summary and the briefing stay short, and checks close tasks without anyone spending effort on them.

```bash
# Before work: what is open, what should I know?
curl -H "Authorization: Bearer $TOKEN" https://your-host/api/projects/my-project

# Urgent tasks across all projects, one line each
curl -H "Authorization: Bearer $TOKEN" "https://your-host/api/todos?prio=1"

# While working
curl -X POST -H "Authorization: Bearer $TOKEN" https://your-host/api/todos/42/done
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"text": "Decided: SQLite is enough, no Postgres", "pinned": true}' \
     https://your-host/api/projects/my-project/notes

# When done
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"text": "Fixed the login redirect"}' https://your-host/api/projects/my-project/log
```

See [Working with agents](docs/agents.md).

## Status and limits

- One admin account, no per-user permissions. Put the app behind HTTPS if it is reachable from the internet, ideally with an access layer in front.
- SQLite only. It is plenty for hundreds of projects and many thousands of tasks.
- Some stored values are German for historical reasons: project status `aktiv`, `pause`, `archiv` and task kind `todo`, `idee`. The interface shows translated labels. The [API reference](docs/api.md) lists the exact values.
- Documents and notes are plain Markdown, sanitized when rendered. There are no file uploads.
- The desktop terminal handler is for Windows.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
