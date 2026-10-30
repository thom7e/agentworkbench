# Briefing und Prüfregeln

[English](../briefing-and-checks.md) · Deutsch

Drei kleine Ideen halten das Dashboard kurz und aktuell: ein **live-Schalter** an Projekten, ein **Kurztitel** an Aufgaben und **Prüfregeln**, die Aufgaben von allein schließen. Zusammen speisen sie das Morgen-Briefing.

## Der live-Schalter

Ein Projekt ist **live**, wenn es produktiv läuft oder beim Kunden ist. Alles andere (Ideen, Experimente, interne Werkzeuge in Entwicklung) ist es nicht.

- Setze ihn mit dem Haken **live** auf der Projektseite, in der Liste unter **Briefing → Projekte im Briefing** oder per API (`PATCH /api/projects/{slug}` mit `{"live": 1}`).
- Live-Projekte stehen im **Seitenmenü** (Desktop) mit einer Lampe, die rot ist, wenn eine Aufgabe mit Priorität 1 offen ist, und im Teil **Dringend** des Briefings.
- Projekte, die nicht live sind, erscheinen im Briefing nur als eine Zeile mit der Anzahl offener Aufgaben.

## Kurztitel

Jede Aufgabe kann einen **Kurztitel** tragen: eine Zeile in einfacher Sprache, ohne Pfade, Befehle oder Fachjargon, so wie du es jemandem sagen würdest, der nicht technisch ist. Der Text kann weiterhin alle Details enthalten.

- Agenten senden ihn als `short`, wenn sie eine Aufgabe anlegen (siehe [API](api.md#aufgaben)). Der Claude-Code-Skill in `examples/claude-code` verlangt ihn.
- Ohne Kurztitel kürzt das Dashboard den Text automatisch (erster Satz, Auszeichnung und Code entfernt). Das funktioniert, aber ein von Hand geschriebener Titel liest sich besser.

## Das Morgen-Briefing

`digest.py` baut einen kurzen Text und sendet ihn als Push-Benachrichtigung. Derselbe Text steht auf der Seite `/briefing`.

Was darin steht:

1. **Dringend: live oder beim Kunden.** Jedes Live-Projekt mit offenen Aufgaben der Priorität 1 oder 2: Projektname fett, bis zu drei Kurztitel, `(+N weitere)` für den Rest. Projekte mit den meisten dringenden Aufgaben stehen zuerst.
2. **Sonst offen.** Eine Zeile: Projektnamen mit der Anzahl ihrer Aufgaben, die größten zuerst (bis zu 20).
3. **Länger offen.** Aufgaben, die länger als 30 Tage offen sind, nach Projekt.
4. **Pull Requests.** Offene Pull Requests deines GitHub-Kontos, wenn GitHub verbunden ist.

Bewusst weggelassen: pausierte und archivierte Projekte, Aufgaben mit Priorität 3, Ideen und alles Erledigte. Der Text folgt der Sprache der Oberfläche (Deutsch oder Englisch) und begrüßt dich mit dem Vornamen aus **Verwaltung → Einstellungen → Dein Vorname**.

Die Benachrichtigung zeigt die ersten Zeilen. Ein Tipp öffnet `/briefing` mit dem vollen Text. Darunter findest du die Projektliste mit einem Haken je Projekt: Das ist der live-Schalter. Änderungen gelten sofort.

Das tägliche Senden ist ein Zeitgeber auf deinem Server, siehe [Betrieb → Morgen-Briefing und Prüfregeln](deployment.md#morgen-briefing-und-prüfregeln). Benachrichtigungen werden in [Handy und Desktop](phone-and-desktop.md#benachrichtigungen) erklärt.

## Prüfregeln

Eine **Prüfregel** ist ein kleiner Maschinentest an einer Aufgabe. Besteht er, wird die Aufgabe automatisch abgehakt, ein Eintrag im Projektverlauf geschrieben (`Automatisch abgehakt (Prüfregel): ...`) und du bekommst eine Benachrichtigung.

### Eine Prüfregel schreiben

Eine Prüfregel ist ein JSON-Objekt oder eine Liste von Objekten, die **alle** bestehen müssen:

| Typ | Felder | Besteht, wenn |
|---|---|---|
| `http` | `url`, optional `status` (Standard 200), `contains`, `not_contains`, `location_contains` | Die Seite mit diesem Status antwortet und die Textbedingungen gelten. Bei `location_contains` werden Weiterleitungen nicht verfolgt, und der `Location`-Header muss den Text enthalten |
| `dns` | `host`, `ip` | Der Host zu dieser Adresse aufgelöst wird |
| `port` | `host`, `port` | Eine TCP-Verbindung aufgebaut werden kann |

Beispiele:

```json
{"type": "http", "url": "https://example.com/robots.txt", "contains": "Sitemap:"}
{"type": "http", "url": "http://example.com/", "status": 301, "location_contains": "https://example.com/"}
[{"type": "dns", "host": "www.example.com", "ip": "203.0.113.10"}, {"type": "port", "host": "www.example.com", "port": 443}]
```

Füge eine Prüfregel beim Anlegen der Aufgabe hinzu (Feld `check`, ein JSON-**String**) oder später mit `PATCH /api/todos/{id}`:

```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"check": "{\"type\":\"http\",\"url\":\"https://example.com/\",\"contains\":\"Willkommen\"}"}' \
     $URL/api/todos/42
```

### Faustregeln

- **Nur die ganze Aufgabe belegen.** Deckt die Prüfregel nur einen Teil ab, würde die Aufgabe zu früh geschlossen. Kombiniere mehrere Bedingungen in einer Liste.
- Eine Prüfregel, die **nicht laufen kann** (Seite nicht erreichbar, ungültiges JSON), zählt als *nicht bestanden*. Sie schließt nie versehentlich eine Aufgabe.
- Prüfregeln laufen vom Server, auf dem das Dashboard läuft, und sehen nur, was dieser Server erreicht. Sie melden sich nirgends an und lesen höchstens 2 MB einer Seite.
- Aufgaben, die an Menschen hängen („Kunden fragen“, „entscheiden“), lassen sich nicht prüfen. Überlasse sie dem Abschluss-Check deines Agenten oder dir.

### Ausführen

`checks.py` führt alle Prüfregeln offener Aufgaben einmal aus. `python checks.py --dry` meldet nur und ändert nichts. Ein täglicher Zeitgeber steht im [Betrieb](deployment.md#morgen-briefing-und-prüfregeln). Das letzte Ergebnis jeder Prüfregel wird an der Aufgabe gespeichert.
