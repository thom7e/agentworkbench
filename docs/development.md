# Development

## Layout

```
app.py            Routes for the pages and the API, setup and login
admin.py          Admin area (settings, projects, tokens, data)
auth.py           Password hashing, sessions, API tokens, request middleware
db.py             Schema and migrations
settings.py       Settings stored in the database
github.py         GitHub data with a short cache
proxmox.py        Read-only Proxmox data with a short cache
render.py         Jinja environment, Markdown rendering, formatting filters
i18n.py           Texts for the admin area, login and setup (de, en)
i18n_ui.py        Texts for the home, project and search pages (de, en)
templates/        Jinja templates
static/           CSS, icons and the web app manifest
scripts/          demo_seed.py (demo data), screenshots.py (README images)
tests/            pytest suite
examples/         Claude Code skill, systemd unit, proxy configs
```

No build step, no JavaScript framework. The few scripts (drag and drop, filter, scroll position) are inline in the templates.

## Run from source

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
AGENTWORKBENCH_DB=./dev.db uvicorn app:app --reload
```

Fill it with demo data first if you like: `AGENTWORKBENCH_DB=./dev.db python scripts/demo_seed.py`.

## Tests

```bash
pytest
```

The tests start the app against a temporary database and cover setup, login, the API, the inbox, notes, documents, search, the Proxmox integration (with a faked Proxmox), translations and the demo data. The CI workflow in `.github/workflows/ci.yml` runs them and also builds the Docker image, starts it and checks the health endpoint.

## Database changes

`db.py` creates missing tables at start and applies additive migrations from the `MIGRATIONS` list (`ALTER TABLE ... ADD COLUMN`, errors for existing columns are ignored). To add a column, add it to the table definition **and** to `MIGRATIONS` so existing databases get it.

## Translations

Texts are keyed: `_('inbox.title')` in templates, `t('key')` in Python. Add a key to both dictionaries in `i18n.py` or `i18n_ui.py`. Texts with placeholders use `{name}` and are called with keyword arguments: `_('row.open', n=3)`.

To add a language, add its code to the dictionaries (`TEXTS` in `i18n.py`, a new dictionary next to `UI_DE` and `UI_EN` in `i18n_ui.py`), and to the allowed values in `render.lang()` and in `settings_save` in `admin.py`, then add an option to `admin_settings.html`. Missing keys fall back to English.

## Screenshots

The images in the README come from the demo data:

```bash
pip install playwright
AGENTWORKBENCH_DB=./demo.db python scripts/demo_seed.py
AGENTWORKBENCH_DB=./demo.db uvicorn app:app --port 8777 &
python scripts/screenshots.py http://127.0.0.1:8777
```

The script drives the Chrome that is installed on your machine and writes to `docs/images`.

## Conventions

- Keep it small: no framework additions without a clear need.
- Routes that change data redirect back (post, redirect, get). Forms carry a hidden `next` field where the page should be kept.
- Do not put personal data, hostnames or tokens into the repository. Use the demo data for examples and screenshots.
