# Betrieb

[English](../deployment.md) · Deutsch

AgentWorkbench ist ein Prozess und eine SQLite-Datei. Wähle, was zu deinem Aufbau passt.

## Docker Compose

```bash
git clone https://github.com/thom7e/agentworkbench.git
cd agentworkbench
docker compose up -d
```

- Die Daten liegen im benannten Volume `agentworkbench-data` (`/data/dashboard.db` im Container).
- Der Container läuft als unprivilegierter Benutzer und hat einen Health-Check auf `/healthz`.
- Ändere den veröffentlichten Port in `docker-compose.yml`, wenn 8000 belegt ist.

Aktualisieren:

```bash
git pull
docker compose up -d --build
```

Datenbankänderungen werden beim Start automatisch eingespielt.

## Reines Python mit systemd

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

Die Unit in [`examples/deploy/agentworkbench.service`](../../examples/deploy/agentworkbench.service) startet `uvicorn` auf Port 8000 mit der Datenbank in `/var/lib/agentworkbench`. Aktualisieren mit `git pull && sudo ./venv/bin/pip install -r requirements.txt && sudo systemctl restart agentworkbench`.

## HTTPS und Reverse-Proxy

Ist die App von außerhalb deines Heim- oder Büronetzes erreichbar, stelle sie hinter HTTPS und sage ihr das:

```
AGENTWORKBENCH_COOKIE_SECURE=1
```

Beispiele für [Caddy](../../examples/deploy/Caddyfile) und [nginx](../../examples/deploy/nginx.conf) liegen in `examples/deploy`. Zwei Einzelheiten zählen:

- Der Proxy muss den ursprünglichen **Host**-Header durchreichen. Die App lehnt Formular-Posts ab, deren `Origin` nicht zum Host passt.
- Anmeldeversuche werden pro Client-IP begrenzt. Uvicorn vertraut `X-Forwarded-For` standardmäßig nur von `127.0.0.1`. Läuft dein Proxy in einem anderen Container oder auf einer anderen Maschine, setze `FORWARDED_ALLOW_IPS` auf die Proxy-Adresse (oder `*`, wenn die App nur über den Proxy erreichbar ist). Sonst wirkt jede Anmeldung, als käme sie vom Proxy.

Alternativen zu einem offenen Port: ein VPN wie WireGuard oder Tailscale, oder ein Tunnel mit Zugriffsregel davor, zum Beispiel Cloudflare Tunnel mit Cloudflare Access. Die App hat eine eigene Anmeldung, aber eine zusätzliche Schicht davor kostet wenig.

## Morgen-Briefing und Prüfregeln

Zwei kleine Skripte laufen zeitgesteuert (systemd-Zeitgeber oder cron) neben der Web-App, mit derselben `AGENTWORKBENCH_DB`:

| Skript | Wann (Beispiel) | Was es tut |
|---|---|---|
| `checks.py` | täglich 06:00 | Führt die [Prüfregeln](briefing-and-checks.md#prüfregeln) offener Aufgaben aus, hakt bestandene ab, sendet eine Benachrichtigung. `--dry` meldet nur |
| `digest.py` | täglich 07:00 | Baut das [Briefing](briefing-and-checks.md#das-morgen-briefing) und sendet es als Push-Benachrichtigung. `--print` gibt es nur aus |

Eine systemd-Unit und ein Zeitgeber für das Briefing (Pfade anpassen, für `checks.py` wiederholen):

```ini
# /etc/systemd/system/agentworkbench-digest.service
[Service]
Type=oneshot
User=awb
WorkingDirectory=/opt/agentworkbench
Environment=AGENTWORKBENCH_DB=/var/lib/agentworkbench/dashboard.db
ExecStart=/opt/agentworkbench/venv/bin/python digest.py

# /etc/systemd/system/agentworkbench-digest.timer
[Timer]
OnCalendar=*-*-* 07:00:00
Persistent=true
[Install]
WantedBy=timers.target
```

Aktivieren mit `sudo systemctl enable --now agentworkbench-digest.timer`. `Persistent=true` holt einen verpassten Lauf nach, wenn der Server aus war.

Voraussetzungen:

- **HTTPS** für Push-Benachrichtigungen und Passkeys und die auf dem Handy installierte App, siehe [Handy und Desktop](phone-and-desktop.md).
- Trage **Kontakt für Push-Nachrichten** und **Dein Vorname** in den Einstellungen ein.
- `pip install -r requirements.txt` nach einem Update bringt die Bibliotheken für Push und Passkeys; der Push-Schlüssel wird beim ersten Gebrauch erzeugt.

## Backups

Alles liegt in der Datenbankdatei, auch Einstellungen, Tokens (als Hash) und der Hash des Admin-Passworts.

**Konsistente Kopie, während die App läuft** (gilt für beide Installationen):

```bash
python3 - <<'EOF'
import sqlite3
src = sqlite3.connect("/var/lib/agentworkbench/dashboard.db")
dst = sqlite3.connect("/backup/dashboard-backup.db")
src.backup(dst)
EOF
```

Mit Docker:

```bash
docker exec agentworkbench python -c "import sqlite3; s=sqlite3.connect('/data/dashboard.db'); d=sqlite3.connect('/data/backup.db'); s.backup(d)"
docker cp agentworkbench:/data/backup.db ./dashboard-backup.db
```

**Wiederherstellen:** App stoppen, die Datei als `dashboard.db` zurücklegen, App starten.

**Portabler Export:** **Verwaltung → Daten → Alles als JSON herunterladen** enthält Projekte, Aufgaben, Verlauf, Notizen und Dokumente, aber keine Einstellungen oder Tokens. Praktisch, um Inhalte zwischen Instanzen zu verschieben.

Plane das Backup ein (cron, systemd-Zeitgeber) und teste einmal eine Wiederherstellung.

## Admin-Passwort zurücksetzen

Es gibt ein Admin-Konto. Hast du das Passwort vergessen, entferne seinen Hash und lege auf der Einrichtungsseite ein neues fest:

```bash
python3 -c "import sqlite3; c = sqlite3.connect('dashboard.db'); c.execute(\"DELETE FROM settings WHERE key IN ('admin_hash','secret_key')\"); c.commit()"
```

Öffne dann `/setup`. Das Entfernen von `secret_key` meldet auch jede bestehende Sitzung ab. Solange kein Passwort gesetzt ist, kann der erste Besucher eines wählen, mache das also in einem Netz, dem du vertraust. Mit Docker führst du denselben Befehl im Container aus, mit `/data/dashboard.db`.

## Auf einen anderen Server umziehen

App stoppen, `dashboard.db` auf den neuen Host kopieren, App dort starten. Einstellungen, Tokens und Passwort ziehen mit um. Setze `AGENTWORKBENCH_COOKIE_SECURE` passend zum neuen Aufbau. Ändert sich die Domain, lege Passkeys und Push-Anmeldungen neu an.

## Ressourcen

Die App ist leicht: einige Dutzend MB Arbeitsspeicher und keine Hintergrundprozesse. GitHub- und Proxmox-Daten werden bei Bedarf geholt und ein bis zehn Minuten zwischengespeichert.
