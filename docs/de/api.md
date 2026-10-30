# API-Referenz

[English](../api.md) · Deutsch

Basis-URL: die Adresse deiner Instanz, zum Beispiel `https://workbench.example.com`.

## Authentifizierung

Sende einen Token im `Authorization`-Header:

```
Authorization: Bearer wb_...
```

Lege Tokens unter **Verwaltung → API-Zugänge** an. Für die Seiten funktioniert auch eine angemeldete Browser-Sitzung. Ohne gültigen Token antwortet die API mit `401`.

Anfrage-Bodies sind JSON (`Content-Type: application/json`, UTF-8). Unbekannte Felder werden ignoriert. Unbekannte Projekte, Aufgaben, Notizen oder Dokumente antworten mit `404`.

## Werte

| Feld | Werte |
|---|---|
| `status` | `aktiv` (aktiv), `pause` (pausiert), `archiv` (archiviert) |
| `kind` | `todo` (Aufgabe), `idee` (Idee) |
| `prio` | `1` dringend, `2` normal, `3` irgendwann |
| `live` | `1` live oder beim Kunden, `0` nicht |

## Überblick und Briefing

### `GET /api/overview`

Klartext, ein Projekt pro Zeile, durch Tabulator getrennt: `slug`, `status`, `N open (M P1)`, `name`, `hosting`.

```bash
curl -H "Authorization: Bearer $TOKEN" $URL/api/overview
```

### `GET /api/projects/{slug}`

Das Briefing als Markdown:

```
# Projektname (slug) — aktiv
Deploy: ...            Hosting, Stack, Repo, verlinkte Notizen, Wiki (nur wenn gesetzt)
Runs on: LXC 137 ...   nur mit der Proxmox-Anbindung
Zusammenfassung

## Documents (lesen mit GET /api/docs/<id>)
## Pinned notes
## Recent notes        die letzten 5 nicht angepinnten Notizen
## Open                offene Aufgaben als "- [ ] #id (P1) Text"
## Ideas
## Recently done       die letzten 5
## Log                 die letzten 8 Einträge
```

Die Aufgaben-IDs im Briefing sind die IDs, die die folgenden Endpunkte verwenden.

## Projekte

### `PUT /api/projects`

Projekt anlegen oder vollständig ersetzen. Nicht gesendete Felder werden auf ihre Standardwerte zurückgesetzt, außer `live`, das dieser Aufruf nie ändert (nimm `PATCH`).

```json
{"slug": "website", "name": "Website-Relaunch", "status": "aktiv", "area": "Kundenseiten",
 "deploy": "VPS", "stack": "Django", "summary": "Relaunch für die Bäckerei",
 "vault_note": "https://example.com/spec", "repo": "me/website", "wiki": "", "vmid": 0}
```

`slug` und `name` sind Pflicht. `area` sollte eine der Gruppen aus den Einstellungen sein. `vault_note` (ein historischer Name) nimmt eine Webadresse pro Zeile, sie erscheinen als Links auf der Projektseite.

### `PATCH /api/projects/{slug}`

Ändert nur die gesendeten Felder. Akzeptiert `name`, `status`, `area`, `deploy`, `stack`, `summary`, `vault_note`, `repo`, `wiki`, `vmid` und `live`.

```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"status": "pause"}' $URL/api/projects/website
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"live": 1}' $URL/api/projects/website
```

## Aufgaben

### `POST /api/projects/{slug}/todos`

```json
{"text": "Ratenbegrenzung am Login einbauen", "short": "Login-Versuche begrenzen", "prio": 1, "kind": "todo", "check": ""}
```

| Feld | Bedeutung |
|---|---|
| `text` | Die volle Beschreibung, Details erlaubt. Pflicht |
| `short` | Einzeiliger Titel in einfacher Sprache, wird im Briefing verwendet. Ohne ihn wird der Text automatisch gekürzt |
| `prio` | Standard `2` |
| `kind` | Standard `todo` |
| `check` | Optionale Maschinenprüfung als JSON-**String**, siehe [Briefing und Prüfregeln](briefing-and-checks.md#prüfregeln). Besteht sie, wird die Aufgabe automatisch abgehakt |

Antwortet mit `{"id": 42}`. Über die API angelegte Aufgaben sind als von einem Agenten stammend markiert und erscheinen im **Posteingang**, bis ein Mensch sie übernimmt, abschließt oder verwirft.

### `PATCH /api/todos/{id}`

Ändert `project` (in ein anderes Projekt verschieben), `text`, `short`, `check`, `prio` oder `kind`.

```json
{"project": "anderes-projekt", "prio": 1}
```

### `POST /api/todos/{id}/done`

Markiert eine Aufgabe als erledigt und schreibt einen Verlaufseintrag.

## Verlauf

### `POST /api/projects/{slug}/log`

```json
{"text": "Login-Weiterleitung repariert (abc123)"}
```

## Notizen

### `POST /api/projects/{slug}/notes`

```json
{"text": "Entschieden: SQLite reicht, kein Postgres. Grund: ein einzelner Schreiber.", "pinned": true}
```

Antwortet mit `{"id": 7}`. Die Notiz ist als von einem Agenten geschrieben markiert. Angepinnte Notizen sind immer Teil des Briefings.

### `PUT /api/notes/{id}`

Ersetzt Text und Pin-Status einer Notiz: `{"text": "...", "pinned": false}`. Nützlich, um eine synchronisierte Kopie einer externen Quelle aktuell zu halten, statt Duplikate anzulegen.

## Dokumente

### `POST /api/projects/{slug}/docs`

```json
{"title": "Betriebshandbuch", "body": "# Betriebshandbuch\n\n1. ...", "source": ""}
```

Antwortet mit `{"id": 3}`. `body` ist Markdown.

### `GET /api/docs/{id}`

Liefert das Dokument als Markdown-Text, beginnend mit dem Titel als Überschrift.

### `PUT /api/docs/{id}`

Ersetzt Titel und Text: `{"title": "...", "body": "..."}`. Lies das Dokument zuerst und sende den vollständigen Text zurück.

## Suche

### `GET /api/search?q=begriff`

Klartext, ein Treffer pro Zeile: `note #7 [slug] Datum: Text`, `doc #3 [slug] Titel`, `todo #42 [slug] open|done: Text`, `project slug: Name`. Antwortet mit `no results`, wenn nichts passt. Die Suche ist ein Teilstring-Vergleich ohne Beachtung der Groß-/Kleinschreibung.

## Exporte

| Endpunkt | Liefert |
|---|---|
| `GET /export/todo.md` | Die Briefings aller aktiven Projekte, aneinandergehängt, als Markdown |
| `GET /export/notes.md` | Alle Notizen nach Projekt gruppiert |

## Health-Check

`GET /healthz` liefert `ok` und braucht keine Authentifizierung.

## Endpunkte nur für den Browser

Diese nutzt die Weboberfläche, sie brauchen eine angemeldete Browser-Sitzung, keinen Token. Sie stehen hier der Vollständigkeit halber.

| Endpunkt | Zweck |
|---|---|
| `GET /briefing` | Die Briefing-Seite |
| `GET /push/key`, `POST /push/subscribe`, `POST /push/test` | Ein Gerät für Push-Benachrichtigungen anmelden und einen Test senden |
| `GET /passkey/register/options`, `POST /passkey/register/verify`, `POST /passkey/{id}/delete` | Passkeys hinzufügen und entfernen |
| `GET /passkey/login/options`, `POST /passkey/login/verify` | Passkey-Anmeldung (öffentlich) |
| `GET /sw.js` | Der Service Worker (öffentlich) |
