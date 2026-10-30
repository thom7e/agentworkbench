# AgentWorkbench

[![CI](https://github.com/thom7e/agentworkbench/actions/workflows/ci.yml/badge.svg)](https://github.com/thom7e/agentworkbench/actions/workflows/ci.yml)

[English](README.md) · Deutsch

**Eine gemeinsame Sicht auf alle Projekte, für dich und deine KI-Agenten. Deine Agenten lesen nicht mehr ganze Dateien, sondern starten mit etwa 100 bis 400 Tokens Kontext.**

> **Warum das Tokens spart**
> Ohne gemeinsames Gedächtnis liest jeder Agent zu Beginn Notizen, TODO-Dateien und alte Chats: schnell 5.000 bis 20.000 Tokens, und beim nächsten Mal wieder. AgentWorkbench gibt dem Agenten stattdessen ein kurzes Briefing pro Projekt.
>
> | Gemessen an einer echten Instanz (89 Projekte, 90 Dokumente) | Tokens |
> |---|---|
> | Übersicht aller Projekte | etwa 1.700 |
> | Briefing eines Projekts, Median / Durchschnitt | etwa 120 / 420 |
> | Dokumente, nur bei Bedarf gelesen (Durchschnitt je Dokument) | etwa 2.600 |
>
> Geschätzte Ersparnis: **etwa 90 % der Kontext-Tokens pro Sitzung**, von 5.000 bis 20.000 auf wenige hundert. Prüfregeln und Morgen-Briefing laufen ganz ohne KI und kosten keine Tokens. (Die Ersparnis ist eine Schätzung auf Basis typischer Notiz- und TODO-Dateien. Die Größen sind gemessen, 1 Token wird mit 3,6 Zeichen gerechnet.)

AgentWorkbench ist ein kleines Dashboard zum Selbsthosten. Du öffnest es morgens (oder bekommst es als Benachrichtigung) und siehst, was zählt: was live und beim Kunden ist, was dringend ist, was deine Agenten getan haben und was sich auf GitHub geändert hat. Agenten wie [Claude Code](https://claude.com/claude-code) lesen vor der Arbeit ein kurzes Briefing, haken Aufgaben ab und hinterlassen Notizen für das nächste Mal. So muss nichts zweimal erklärt werden.

Ein FastAPI-Prozess, eine SQLite-Datei, kein Build-Schritt. Oberfläche auf Deutsch und Englisch, auf dem Handy als App installierbar.

<p align="center">
  <img src="docs/images/dashboard-light.png" alt="Startseite mit Seitenmenü, dringenden Aufgaben und Verlauf" width="860">
</p>
<p align="center">
  <img src="docs/images/briefing.png" alt="Die Briefing-Seite" width="420">
  <img src="docs/images/mobile.png" alt="Handy: Heute" width="190">
  <img src="docs/images/mobile-projects.png" alt="Handy: Projekte" width="190">
</p>

## Funktionen

**Überblick**
- **Heute zuerst**: alle dringenden Aufgaben über alle Projekte in einer Liste, direkt abhakbar.
- **Projekte** in Gruppen nach Wahl, mit einem **live**-Schalter für alles, was für Kunden oder produktiv läuft. Live-Projekte stehen mit einer Lampe im Seitenmenü, die rot wird, wenn etwas dringend ist.
- **Projektseiten** mit Reitern: Aufgaben und Ideen, Notizen, Dokumente und ein Verlauf-Reiter mit Protokoll, Git-Branches und letzten Commits.
- **Posteingang** für Aufgaben, die Agenten seit deinem letzten Blick angelegt haben: *Übernehmen*, *Bereits erledigt* oder *Verwerfen*. Offene Pull Requests erscheinen dort auch.
- **Prioritäts-Board** (Karte ziehen, um die Priorität zu ändern) und **Suche** über Notizen, Dokumente, Aufgaben und Projekte.

**Briefing und Automatik**
- **Morgen-Briefing** als Push-Benachrichtigung: Live-Projekte zuerst mit einer verständlichen Zeile pro Aufgabe, alles andere in einer Zeile, ein Hinweis auf Aufgaben, die länger als 30 Tage offen sind. Ein Tipp öffnet die Briefing-Seite, auf der du wählst, welche Projekte als live gelten.
- **Prüfregeln, die Aufgaben für dich abhaken**: Eine Aufgabe kann eine kleine Maschinenprüfung tragen (Seite liefert 200, Text vorhanden, Weiterleitung, DNS, offener Port). Ein täglicher Lauf hakt sie ab, schreibt einen Verlaufseintrag und benachrichtigt dich.
- **Notizen als Gedächtnis**: Notizen mit Zeitstempel von dir oder einem Agenten, anpinnbar. Agenten bekommen die angepinnten und die letzten Notizen bei jedem Briefing.

**Für Agenten**
- Ein kompaktes **Briefing** pro Projekt (Markdown, kurz), eine kleine **HTTP-API** mit widerrufbaren Tokens und ein fertiger [Claude-Code-Skill](examples/claude-code).

**Handy und Desktop**
- **Handy-App**: auf den Home-Bildschirm legen. Sie liest offline, hat einen Schnell-Eintrag mit Offline-Warteschlange, Wischen zum Abhaken, Ziehen zum Aktualisieren und Web-Push.
- **Passkey-Anmeldung** (Face ID, Touch ID, Windows Hello) neben dem Passwort.
- **Desktop-Terminal** (optional, Windows): Ein Knopf an jeder Aufgabe öffnet ein Terminal im Projektordner mit deinem KI-Agenten und der Aufgabe als Startauftrag.

**Betrieb**
- Optionale, nur lesende **Proxmox**-Anbindung (Status und IP pro Projekt), **Adminbereich** mit Einstellungen, Projekten, API-Zugängen, JSON-Backup und Markdown-Import. Helles und dunkles Design folgen deinem System.

## Schnellstart

### Docker (empfohlen)

```bash
git clone https://github.com/thom7e/agentworkbench.git
cd agentworkbench
docker compose up -d
```

Dann <http://localhost:8000> öffnen. Beim ersten Besuch legst du das Admin-Passwort fest. Die Daten liegen im Volume `agentworkbench-data`. Die Sprache stellst du unter **Verwaltung → Einstellungen** auf Deutsch.

### Python

```bash
git clone https://github.com/thom7e/agentworkbench.git
cd agentworkbench
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Mit Demodaten ausprobieren

```bash
AGENTWORKBENCH_DB=./demo.db python scripts/demo_seed.py
AGENTWORKBENCH_DB=./demo.db uvicorn app:app
```

Anmelden mit `demo-password-123`. Die Demo enthält erfundene Projekte, einen Posteingang, Notizen und Dokumente.

> Passkeys und Push-Benachrichtigungen brauchen HTTPS (eine echte Domain oder `localhost`). Siehe [Betrieb](docs/de/deployment.md#https-und-reverse-proxy).

## Dokumentation

| Anleitung | Inhalt |
|---|---|
| [Erste Schritte](docs/de/getting-started.md) | Erster Start, erstes Projekt, täglicher Ablauf |
| [Konfiguration](docs/de/configuration.md) | Jede Einstellung und Umgebungsvariable |
| [Briefing und Prüfregeln](docs/de/briefing-and-checks.md) | Der live-Schalter, Kurztitel, das Morgen-Briefing, Maschinenprüfungen |
| [Handy und Desktop](docs/de/phone-and-desktop.md) | Handy-App, Benachrichtigungen, Passkeys, das Desktop-Terminal |
| [Mit Agenten arbeiten](docs/de/agents.md) | Das Briefing, Notiz oder Protokoll, ein fertiger Claude-Code-Skill |
| [API-Referenz](docs/de/api.md) | Alle Endpunkte mit Beispielen |
| [Proxmox-Anbindung](docs/de/proxmox.md) | Lesender Token, Projekte mit Containern verknüpfen |
| [Betrieb](docs/de/deployment.md) | Docker, systemd, HTTPS, Zeitgeber, Backups, Updates, Passwort zurücksetzen |
| [Sicherheit](docs/de/security.md) | Was geschützt ist und was nicht |
| [Entwicklung](docs/de/development.md) | Aufbau, Tests, Übersetzungen, Screenshots |

Jede Anleitung gibt es auch auf Englisch im Ordner [`docs`](docs).

## Warum Agenten es mögen

Ein Agent muss wissen, was offen ist, was entschieden wurde und wo etwas läuft, ohne ganze Dateien zu lesen. Das Briefing ist ein kurzer Markdown-Text pro Projekt: offene Aufgaben mit Priorität, angepinnte und letzte Notizen, eine Liste der Dokumente (bei Bedarf lesen) und die letzten Protokolleinträge. Aufgaben tragen einen einzeiligen Titel, damit die Morgen-Zusammenfassung und das Briefing kurz bleiben. Prüfregeln schließen Aufgaben, ohne dass jemand Aufwand hat.

```bash
# Vor der Arbeit: was ist offen, was sollte ich wissen?
curl -H "Authorization: Bearer $TOKEN" https://dein-host/api/projects/mein-projekt

# Während der Arbeit
curl -X POST -H "Authorization: Bearer $TOKEN" https://dein-host/api/todos/42/done
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"text": "Entschieden: SQLite reicht, kein Postgres", "pinned": true}' \
     https://dein-host/api/projects/mein-projekt/notes

# Am Ende
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"text": "Login-Weiterleitung repariert"}' https://dein-host/api/projects/mein-projekt/log
```

Siehe [Mit Agenten arbeiten](docs/de/agents.md).

## Stand und Grenzen

- Ein Admin-Konto, keine Rechte pro Benutzer. Stelle die App hinter HTTPS, wenn sie aus dem Internet erreichbar ist, am besten mit einer Zugriffsschicht davor.
- Nur SQLite. Das reicht für Hunderte Projekte und viele tausend Aufgaben.
- Einige gespeicherte Werte sind aus historischen Gründen deutsch: Projektstatus `aktiv`, `pause`, `archiv` und Aufgabenart `todo`, `idee`. Die Oberfläche zeigt übersetzte Bezeichnungen. Die [API-Referenz](docs/de/api.md) nennt die genauen Werte.
- Dokumente und Notizen sind einfaches Markdown, beim Anzeigen bereinigt. Es gibt keine Datei-Uploads.
- Der Handler für das Desktop-Terminal ist für Windows.

## Mitmachen und Sicherheit

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) und [SECURITY.md](SECURITY.md).

## Lizenz

[MIT](LICENSE)
