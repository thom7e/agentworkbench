# Mit Agenten arbeiten

[English](../agents.md) · Deutsch

AgentWorkbench ist so gebaut, dass ein KI-Agent ein Projekt übernehmen kann wie ein Kollege: lesen, was offen ist und was entschieden wurde, die Arbeit erledigen und eine Spur hinterlassen.

## Die Idee

1. **Briefing.** Bevor der Agent mit einem Projekt beginnt, holt er einen Markdown-Text mit allem, was er braucht: wo das Projekt läuft, offene Aufgaben mit Priorität, Ideen, angepinnte Notizen, die letzten Notizen, die Dokumentenliste, zuletzt Erledigtes und die letzten Protokolleinträge.
2. **Arbeit.** Während er arbeitet, hakt der Agent Erledigtes ab, legt neue Aufgaben und Ideen an und speichert alles Merkenswerte als Notiz.
3. **Verständliche Titel.** Neue Aufgaben bekommen einen einzeiligen `short`-Titel in einfacher Sprache. Den zeigt das Morgen-Briefing, damit die Zusammenfassung lesbar bleibt. Lässt sich die Erledigung per Test belegen, hängt der Agent außerdem eine [Prüfregel](briefing-and-checks.md#prüfregeln) an, und die Aufgabe schließt sich selbst.
4. **Spur.** Am Ende schreibt er einen Protokolleintrag: was getan wurde, in einem Satz, am besten mit Commit-Hash.
5. **Abschluss-Check.** Bevor er fertig ist, geht er die offenen Aufgaben noch einmal durch und hakt alles ab, was erledigt und belegt ist. Nur teilweise Erledigtes bleibt offen und wird auf den Rest gekürzt. Unsichere Fälle meldet er dir, statt sie abzuhaken. Der Skill und der `CLAUDE.md`-Ausschnitt in `examples/claude-code` machen das zur festen Regel.

Ohne Token wird nichts geschrieben, und jeder Eintrag eines Agenten ist sichtbar: Neue Aufgaben landen in deinem **Posteingang**, bis du sie übernimmst, als erledigt markierst oder verwirfst.

## Protokoll, Notiz oder Dokument?

| | Protokolleintrag | Notiz | Dokument |
|---|---|---|---|
| Antwortet auf | Was wurde getan? | Was sollte ich später noch wissen? | Wie funktioniert es? |
| Länge | Ein Satz | Ein paar Zeilen | Eine Seite oder mehr |
| Beispiele | „Login-Weiterleitung repariert (abc123)“ | „Gegen Postgres entschieden, SQLite reicht. Grund: ein Schreiber“ | Betriebshandbuch, Checkliste, Spezifikation |
| Im Briefing | Die letzten 8 | Angepinnte und die letzten 5 | Nur die Titelliste, bei Bedarf lesen |

Faustregel für Agenten: Wenn es noch zählt, nachdem das Protokoll weitergescrollt ist, ist es eine Notiz.

## Tokens

Lege pro Agent einen Token unter **Verwaltung → API-Zugänge** an. Ein Token wird einmal angezeigt und nur als Hash gespeichert. Du kannst ihn dort jederzeit widerrufen. Tokens geben vollen API-Zugriff, siehe [Sicherheit](security.md).

## Claude Code

Ein fertiger Skill und ein Ausschnitt für deine `CLAUDE.md` liegen in [`examples/claude-code`](../../examples/claude-code).

1. Lege Adresse und Token in einer Datei ab, die nur du lesen kannst, zum Beispiel `~/.claude/agentworkbench.env`:

   ```bash
   AWB_URL=https://workbench.example.com
   AWB_TOKEN=wb_...
   ```

2. Kopiere `examples/claude-code/SKILL.md` nach `~/.claude/skills/agentworkbench/SKILL.md`.
3. Füge den Ausschnitt aus `examples/claude-code/CLAUDE.md.snippet.md` in deine globale `~/.claude/CLAUDE.md` ein, damit jede Sitzung vom Dashboard weiß.

Ab dann holt Claude Code bei der Frage „Was ist in Projekt X offen?“ oder beim Start einer Arbeit am Projekt das Briefing und hält das Dashboard aktuell.

## Jeder andere Agent oder jedes Skript

Die API ist einfaches HTTP mit JSON-Bodies und Bearer-Token, funktioniert also mit jedem Werkzeug. Siehe die [API-Referenz](api.md). Eine minimale Schleife:

```bash
H="Authorization: Bearer $TOKEN"
curl -s -H "$H" "$URL/api/overview"                       # welche Projekte gibt es
curl -s -H "$H" "$URL/api/projects/website"               # Briefing
curl -s -X POST -H "$H" "$URL/api/todos/42/done"          # abhaken
curl -s -X POST -H "$H" -H "Content-Type: application/json" \
     -d '{"text":"Ratenbegrenzung eingebaut (abc123)"}' "$URL/api/projects/website/log"
```

Sende JSON als UTF-8 (`Content-Type: application/json; charset=utf-8`), besonders in Windows-Shells.

## Tipps

- Halte das **Briefing kurz und aktuell**: Archiviere Projekte, an denen du nicht mehr arbeitest, sie verschwinden aus dem Board und dem Briefing.
- Gib Agenten **ein Projekt nach dem anderen**. Der Slug bezeichnet es, `GET /api/overview` listet alle Slugs.
- Bitte Agenten, ein **Dokument zu lesen, bevor sie es ändern**, und nur zu ändern, was nötig ist.
- Lass Agenten keine Geheimnisse in Notizen oder Dokumente schreiben. Bewahre Zugangsdaten in einem Passwortmanager auf.
