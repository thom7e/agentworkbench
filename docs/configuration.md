# Configuration

Almost everything is configured in the admin area. A few values come from the environment because they must be known before the database is opened.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `AGENTWORKBENCH_DB` | `./dashboard.db` (Docker: `/data/dashboard.db`) | Path of the SQLite file |
| `AGENTWORKBENCH_COOKIE_SECURE` | `0` | Set to `1` when you serve the app over HTTPS, so the session cookie is marked `Secure` |
| `AGENTWORKBENCH_TOKEN` | empty | Optional static API token. Tokens created in the admin area are preferred because they can be revoked |
| `GITHUB_TOKEN` | empty | Fallback if no GitHub token is stored in the settings |

## Admin → Settings

| Setting | Meaning |
|---|---|
| **Site title** | Shown in the top bar and the browser tab |
| **Language** | `de` or `en`. Applies to the whole interface |
| **Groups** | One group per line, in the order they appear on the home page. A project whose group is not in this list appears in the first group |
| **Dormant after (days)** | A project with no open tasks and no activity or push for this many days moves into the collapsed *dormant* section of its group. Default 90 |
| **Default sorting** | Order of projects within a group: *recent activity* (newest first, using the later of the last log entry and the last GitHub push) or *open tasks* |
| **GitHub account** | User or organisation whose repositories are listed |
| **GitHub token** | Read-only token, see [Getting started](getting-started.md#optional-github). Leave the field empty to keep the stored token |
| **Your first name** | Optional. Used in the greeting of the morning briefing |
| **Contact for push messages** | A `mailto:` or `https` address sent to push services as the sender contact; Apple requires a valid value for web push to arrive |
| **Proxmox address, token ID, token secret, verify TLS** | Optional, see [Proxmox integration](proxmox.md) |

Settings are stored in the `settings` table of the database. The GitHub token and the Proxmox secret are stored in plain text there, so protect the database file like any other secret.

## Project fields

| Field | Meaning |
|---|---|
| Name, slug | The slug is the stable key used in URLs and the API. It is derived from the name on creation and cannot be changed afterwards |
| Status | `aktiv` (active), `pause` (paused), `archiv` (archived). The tabs on the home page filter by status |
| Group | One of the groups from the settings |
| Hosting, stack | Free text, shown on the project page |
| Summary | One or two sentences, shown below the title and in search |
| GitHub repo | `owner/name`. Enables the Git section and the last-push time |
| Wiki address | Link shown on the project page |
| Notes | Links to external notes (specs, wiki pages), one web address per line |
| Container or VM number | Links the project to a Proxmox guest, see [Proxmox integration](proxmox.md) |

## Data

| Action | Where |
|---|---|
| Download everything as JSON | **Admin → Data → Export** (projects, tasks, activity, notes, documents) |
| Restore a JSON backup | **Admin → Data → Import → Restore a JSON backup**. Projects with the same slug are replaced together with their tasks, notes, documents and activity. Everything else is added |
| Import Markdown | **Admin → Data → Import Markdown** |
| All notes as Markdown | `GET /export/notes.md` |
| All open tasks as Markdown | `GET /export/todo.md` |

The JSON backup does not contain settings, tokens or the admin password. For a complete backup copy the database file, see [Deployment → Backups](deployment.md#backups).
