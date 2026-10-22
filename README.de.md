# AgentWorkbench (Deutsch)

**Eine gemeinsame Sicht auf alle Projekte, für dich und deine KI-Agenten.**

AgentWorkbench ist ein kleines Dashboard zum Selbsthosten. Du öffnest es morgens und siehst, was zählt: dringende Aufgaben, ein Prioritäts-Board über alle Projekte, was deine Agenten getan haben und was sich auf GitHub geändert hat. Agenten wie [Claude Code](https://claude.com/claude-code) lesen vor der Arbeit ein Briefing, haken Aufgaben ab und hinterlassen Notizen für das nächste Mal.

Ein FastAPI-Prozess, eine SQLite-Datei, kein Build-Schritt. Oberfläche auf Deutsch und Englisch, als App auf dem Handy installierbar.

## Funktionen

- Prioritäts-Board über alle Projekte (Karte ziehen, auf dem Handy 1, 2 oder 3 tippen)
- „Heute zuerst“ mit allen dringenden Aufgaben
- Posteingang für neue Aufgaben von Agenten: *Übernehmen*, *Bereits erledigt* oder *Verwerfen*, dazu offene Pull Requests
- Projektseiten mit Aufgaben, Ideen, Verlauf, Branches, letzten Commits und README-Auszug
- Notizen als Projekt-Gedächtnis (anpinnbar), Dokumente in Markdown, Suche über alles
- Gruppen nach Wahl, Sortierung nach Aktualität oder offenen Aufgaben, eingeklappter Bereich „Ruhend“
- Optional: Proxmox-Anbindung (nur lesend) mit Live-Status und IP pro Projekt und Liste aller Container
- Adminbereich: Einstellungen, Projekte, API-Zugänge, Backup und Import
- Agent-API mit widerrufbaren Tokens

## Schnellstart

```bash
git clone https://github.com/thom7e/agentworkbench.git
cd agentworkbench
docker compose up -d
```

Dann <http://localhost:8000> öffnen und beim ersten Besuch das Admin-Passwort festlegen. Unter **Verwaltung → Einstellungen** stellst du die Sprache auf Deutsch.

Ohne Docker, mit Demodaten, Konfiguration, API, Proxmox, Betrieb und Sicherheit: siehe die englische [README](README.md) und die Anleitungen im Ordner [`docs`](docs).

## Lizenz

[MIT](LICENSE)
