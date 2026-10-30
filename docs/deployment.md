# Deployment

AgentWorkbench is one process and one SQLite file. Pick whichever fits your setup.

## Docker Compose

```bash
git clone https://github.com/thom7e/agentworkbench.git
cd agentworkbench
docker compose up -d
```

- The data lives in the named volume `agentworkbench-data` (`/data/dashboard.db` in the container).
- The container runs as an unprivileged user and has a health check on `/healthz`.
- Change the published port in `docker-compose.yml` if 8000 is taken.

Update:

```bash
git pull
docker compose up -d --build
```

Database changes are applied automatically at start.

## Plain Python with systemd

```bash
sudo useradd --system --home /opt/agentworkbench --shell /usr/sbin/nologin awb
sudo git clone https://github.com/thom7e/agentworkbench.git /opt/agentworkbench
cd /opt/agentworkbench
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r requirements.txt
sudo mkdir -p /var/lib/agentworkbench && sudo chown awb:awb /var/lib/agentworkbench
sudo cp examples/deploy/agentworkbench.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now agentworkbench
```

The unit in [`examples/deploy/agentworkbench.service`](../examples/deploy/agentworkbench.service) runs `uvicorn` on port 8000 with the database in `/var/lib/agentworkbench`. Update with `git pull && sudo systemctl restart agentworkbench`.

## HTTPS and reverse proxy

If the app is reachable from outside your home or office network, put it behind HTTPS and tell it so:

```
AGENTWORKBENCH_COOKIE_SECURE=1
```

Examples for [Caddy](../examples/deploy/Caddyfile) and [nginx](../examples/deploy/nginx.conf) are in `examples/deploy`. Two details matter:

- The proxy must pass the original **Host** header. The app rejects form posts whose `Origin` does not match the host.
- Login attempts are rate limited per client IP. Uvicorn trusts `X-Forwarded-For` only from `127.0.0.1` by default. If your proxy runs in another container or on another machine, set `FORWARDED_ALLOW_IPS` to the proxy address (or `*` if the app is only reachable through the proxy). Otherwise every login looks like it comes from the proxy.

Alternatives to opening a port: a VPN such as WireGuard or Tailscale, or a tunnel with an access policy in front, for example Cloudflare Tunnel with Cloudflare Access. The app has its own login, but an extra layer in front costs little.

## Morning briefing and checks

Two small scripts run on a schedule (systemd timers or cron) next to the web app, with the same `AGENTWORKBENCH_DB`:

```ini
# dashboard-digest.service (timer: OnCalendar=*-*-* 07:00:00)
[Service]
Type=oneshot
User=dashboard
WorkingDirectory=/opt/dashboard
Environment=AGENTWORKBENCH_DB=/var/lib/dashboard/dashboard.db
ExecStart=/opt/dashboard/venv/bin/python digest.py
```

- `digest.py` builds the briefing and sends it as a web push (`python digest.py --print` only prints it). Open the app once, tap the bell on the briefing page and allow notifications; on iPhone this only works for the app added to the home screen, over HTTPS.
- `checks.py` runs the machine checks of open tasks (`--dry` only reports). A check is a JSON object, for example `{"type": "http", "url": "https://example.com/robots.txt", "contains": "Sitemap:"}`, or `dns` (`host`, `ip`) or `port` (`host`, `port`); a list means all must pass.
- Passkeys and push need HTTPS (a real domain or `localhost`). Put the app behind a reverse proxy as described above.

## Backups

Everything is in the database file, including settings, tokens (as hashes) and the admin password hash.

**Consistent copy while the app runs** (works for both installs):

```bash
python3 - <<'EOF'
import sqlite3
src = sqlite3.connect("/var/lib/agentworkbench/dashboard.db")
dst = sqlite3.connect("/backup/dashboard-backup.db")
src.backup(dst)
EOF
```

With Docker:

```bash
docker exec agentworkbench python -c "import sqlite3; s=sqlite3.connect('/data/dashboard.db'); d=sqlite3.connect('/data/backup.db'); s.backup(d)"
docker cp agentworkbench:/data/backup.db ./dashboard-backup.db
```

**Restore:** stop the app, put the file back as `dashboard.db`, start the app.

**Portable export:** **Admin → Data → Download everything as JSON** contains projects, tasks, activity, notes and documents, but not settings or tokens. It is handy to move content between instances.

Schedule the backup (cron, systemd timer) and test a restore once.

## Reset the admin password

There is one admin account. If you forgot the password, remove its hash and set a new one on the setup page:

```bash
python3 -c "import sqlite3; c = sqlite3.connect('dashboard.db'); c.execute(\"DELETE FROM settings WHERE key IN ('admin_hash','secret_key')\"); c.commit()"
```

Then open `/setup`. Removing `secret_key` also signs out every existing session. While no password is set, the first visitor can choose one, so do this on a network you trust. With Docker run the same command inside the container using `/data/dashboard.db`.

## Move to another server

Stop the app, copy `dashboard.db` to the new host, start the app there. Settings, tokens and the password move with it. Set `AGENTWORKBENCH_COOKIE_SECURE` according to the new setup.

## Resources

The app is light: a few dozen MB of memory and no background workers. GitHub and Proxmox data is fetched on demand and cached for one to ten minutes.
