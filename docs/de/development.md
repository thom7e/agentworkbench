# Entwicklung

[English](../development.md) · Deutsch

## Aufbau

```
app.py            Routen für Seiten und API, Einrichtung und Anmeldung
admin.py          Adminbereich (Einstellungen, Projekte, Tokens, Daten)
auth.py           Passwort-Hashing, Sitzungen, API-Tokens, Middleware
db.py             Schema und Migrationen
settings.py       In der Datenbank gespeicherte Einstellungen
github.py         GitHub-Daten mit kurzem Zwischenspeicher
proxmox.py        Lesende Proxmox-Daten mit kurzem Zwischenspeicher
render.py         Jinja-Umgebung, Markdown-Darstellung, Formatierfilter
digest.py         Morgen-Briefing: baut den Text, sendet den Push (de, en)
checks.py         Aufgabenprüfungen: führt sie aus, hakt Aufgaben ab, benachrichtigt
push.py           Web-Push: VAPID-Schlüssel, Anmeldungen, Senden
passkeys.py       Passkey-Registrierung und -Anmeldung (WebAuthn)
i18n.py           Texte für Adminbereich, Anmeldung und Einrichtung (de, en)
i18n_ui.py        Texte für Start-, Projekt- und Suchseiten (de, en)
templates/        Jinja-Vorlagen
static/           style.css (Struktur), op.css (Design), app.js (Reiter, Schnell-Eintrag, Wischen,
                  Ziehen zum Aktualisieren), passkey.js, sw.js (Service Worker), Icons, Manifest
desktop/          Windows-Handler für den Terminal-Knopf
scripts/          demo_seed.py (Demodaten), screenshots.py (README-Bilder)
tests/            pytest-Suite
examples/         Claude-Code-Skill, systemd-Unit, Proxy-Konfigurationen
```

Kein Build-Schritt, kein JavaScript-Framework. Einige kleine Skripte stehen inline in den Vorlagen (Drag-and-drop, Filter, Scroll-Position); der Rest liegt in `static/app.js` und `static/passkey.js`.

Statische Dateien werden mit einer Versionsnummer in der URL ausgeliefert (die Zeit der neuesten Datei), und `/sw.js` wird mit derselben Nummer erzeugt, sodass eine neue Bereitstellung installierte Handy-Apps von selbst erreicht.

## Aus dem Quellcode starten

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
AGENTWORKBENCH_DB=./dev.db uvicorn app:app --reload
```

Fülle sie vorher mit Demodaten, wenn du magst: `AGENTWORKBENCH_DB=./dev.db python scripts/demo_seed.py`.

## Tests

```bash
pytest
```

Die Tests starten die App gegen eine temporäre Datenbank und decken Einrichtung, Anmeldung, Passkeys (mit einem Software-Authenticator), die API, den Posteingang, Notizen, Dokumente, Suche, das Briefing, Prüfregeln, Push, die Proxmox-Anbindung (mit gefälschtem Proxmox), Übersetzungen und die Demodaten ab. Der CI-Workflow in `.github/workflows/ci.yml` führt sie aus, baut außerdem das Docker-Image, startet es und prüft den Health-Endpunkt.

## Datenbankänderungen

`db.py` legt fehlende Tabellen beim Start an und spielt additive Migrationen aus der Liste `MIGRATIONS` ein (`ALTER TABLE ... ADD COLUMN`, Fehler bei vorhandenen Spalten werden ignoriert). Um eine Spalte hinzuzufügen, trage sie in die Tabellendefinition **und** in `MIGRATIONS` ein, damit bestehende Datenbanken sie bekommen.

## Übersetzungen

Texte haben Schlüssel: `_('inbox.title')` in Vorlagen, `t('key')` in Python. Füge einen Schlüssel in beide Wörterbücher in `i18n.py` oder `i18n_ui.py` ein. Texte mit Platzhaltern nutzen `{name}` und werden mit Schlüsselwort-Argumenten aufgerufen: `_('row.open', n=3)`. Das Briefing (`digest.py`) und die Prüfmeldungen (`checks.py`) haben ihre kleinen Wörterbücher im Modul selbst.

Um eine Sprache hinzuzufügen, trage ihr Kürzel in die Wörterbücher ein (`TEXTS` in `i18n.py`, ein neues Wörterbuch neben `UI_DE` und `UI_EN` in `i18n_ui.py`, dazu `TEXT` in `digest.py` und `checks.py`) sowie in die erlaubten Werte in `render.lang()` und in `settings_save` in `admin.py`, und füge dann eine Option in `admin_settings.html` ein. Fehlende Schlüssel fallen auf Englisch zurück.

## Screenshots

Die Bilder in der README stammen aus den Demodaten:

```bash
pip install playwright
AGENTWORKBENCH_DB=./demo.db python scripts/demo_seed.py
AGENTWORKBENCH_DB=./demo.db uvicorn app:app --port 8777 &
python scripts/screenshots.py http://127.0.0.1:8777
```

Das Skript steuert das auf deinem Rechner installierte Chrome und schreibt nach `docs/images`.

## Konventionen

- Klein halten: keine Framework-Ergänzungen ohne klaren Bedarf.
- Routen, die Daten ändern, leiten zurück (Post, Redirect, Get). Formulare tragen ein verstecktes Feld `next`, wo die Seite erhalten bleiben soll.
- Keine persönlichen Daten, Hostnamen oder Tokens ins Repository. Nutze für Beispiele und Screenshots die Demodaten.
