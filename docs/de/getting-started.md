# Erste Schritte

[English](../getting-started.md) · Deutsch

Diese Anleitung führt dich in etwa zehn Minuten von einer leeren Installation zu einem täglichen Ablauf.

## 1. App starten

Wähle einen Weg aus der [README](../../README.de.md#schnellstart): Docker, reines Python oder die Demodaten. Die App lauscht auf Port 8000.

## 2. Admin-Passwort festlegen

Der erste Besuch leitet auf `/setup`. Wähle ein Passwort mit mindestens zehn Zeichen. Das ist das einzige Konto: Es schützt das Dashboard und den Adminbereich. Danach bleibst du 30 Tage angemeldet.

Passwort später vergessen? Siehe [Betrieb → Admin-Passwort zurücksetzen](deployment.md#admin-passwort-zurücksetzen). Sobald du HTTPS nutzt, kannst du dich stattdessen mit einem Passkey anmelden, siehe [Handy und Desktop](phone-and-desktop.md#passkeys).

## 3. Grundeinstellungen

Öffne **Verwaltung → Einstellungen** (der Link *Verwaltung* im Seitenmenü, auf dem Handy unter *Mehr*).

| Einstellung | Was tun |
|---|---|
| Titel der Seite | Beliebig, steht in der Kopfzeile und im Browser-Tab |
| Sprache | Deutsch oder Englisch. Gilt für die Oberfläche und das Morgen-Briefing |
| Gruppen | Eine Gruppe pro Zeile, zum Beispiel `Kundenseiten`, `Interne Werkzeuge`, `Infrastruktur`. Danach werden die Projekte in der Ansicht *Projekte* gruppiert |
| Dein Vorname | Wird in der Begrüßung des Morgen-Briefings verwendet |
| GitHub-Konto und Token | Optional, siehe unten |

Alle Einstellungen stehen in der [Konfiguration](configuration.md).

### Optional: GitHub

Mit einem GitHub-Konto und einem lesenden Token zeigen Projektseiten Branches und letzte Commits, die Projektliste zeigt den Zeitpunkt des letzten Pushs, und offene Pull Requests erscheinen im Posteingang und im Briefing.

1. <https://github.com/settings/personal-access-tokens/new> öffnen
2. Resource owner: dein Konto. Repository access: *All repositories* (damit neue Repositories automatisch erscheinen)
3. Repository permissions, alle **Read-only**: *Contents*, *Pull requests*, *Metadata*
4. Den Token unter **Verwaltung → Einstellungen → GitHub-Token** einfügen und deinen Kontonamen eintragen

Ohne Token funktioniert alles andere unverändert.

## 4. Projekte anlegen

Du hast drei Möglichkeiten.

**Im Adminbereich anlegen.** **Verwaltung → Projekte → Neues Projekt**. Trage Name, Gruppe und Status ein und, wenn du willst, Hosting, Stack, eine Zusammenfassung in einem Satz, das GitHub-Repository (`owner/name`), eine Wiki-Adresse und Links zu Notizen (eine Webadresse pro Zeile).

**Aus Markdown importieren.** **Verwaltung → Daten → Markdown importieren**. Überschriften der Ebene 2 werden zu Projekten, Kontrollkästchen zu Aufgaben:

```markdown
## Website-Relaunch
- [ ] Titelbilder komprimieren
- [x] Kontaktformular einrichten

## Heimserver
- [ ] VPN-Schlüssel erneuern
```

**Per API.** Agenten können Projekte selbst anlegen, siehe [API](api.md#projekte).

Entscheide dann, welche Projekte **live** sind (produktiv oder beim Kunden): Setze den Haken *live* auf der Projektseite. Live-Projekte bekommen einen eigenen Abschnitt im Briefing und eine Lampe im Seitenmenü, siehe [Briefing und Prüfregeln](briefing-and-checks.md#der-live-schalter).

## 5. Mit Aufgaben arbeiten

Eine Projektseite hat vier Reiter: **Aufgaben** (offene Aufgaben, Ideen, Erledigtes), **Notizen**, **Dokumente** und **Verlauf** (Protokoll, Git, Hosting). Lege Aufgaben und Ideen an, wähle eine Priorität und hake sie ab. Gib Aufgaben, die du per API anlegst, einen kurzen, verständlichen Titel: Den zeigt das Briefing.

Auf der Startseite:

- **Heute zuerst** listet alle dringenden Aufgaben (Priorität 1) der aktiven Projekte.
- Der **Posteingang** erscheint, wenn Agenten Aufgaben angelegt haben. Wähle je Aufgabe *Übernehmen* (behalten), *Bereits erledigt* (als erledigt ablegen) oder *Verwerfen* (löschen).
- Das **Prioritäts-Board** (am Desktop standardmäßig eingeklappt) zeigt jede offene Aufgabe in drei Spalten. Ziehe eine Karte, um die Priorität zu ändern.
- Auf dem Handy wechselt die untere Leiste zwischen **Heute**, **Projekte**, **Briefing** und **Mehr**. Der **+**-Knopf legt von überall eine Aufgabe an.

## 6. Notizen, Dokumente, Verlauf

| Verwendung | Wofür |
|---|---|
| **Verlauf** | Was getan wurde, ein Satz, in zeitlicher Reihenfolge |
| **Notizen** | Was du in sechs Monaten noch wissen solltest: Entscheidungen samt Grund, Stolperfallen, wie man etwas erreicht. Wichtiges anpinnen |
| **Dokumente** | Längere Markdown-Seiten: Betriebshandbücher, Checklisten, Spezifikationen |

Alles ist über das Suchfeld auf der Startseite durchsuchbar.

## 7. Einen Agenten damit arbeiten lassen

1. **Verwaltung → API-Zugänge → Zugang anlegen**, gib ihm einen Namen wie `claude`. Kopiere den Token, er wird nur einmal angezeigt.
2. Folge [Mit Agenten arbeiten](agents.md), um den Skill für Claude Code einzurichten, oder rufe die [API](api.md) aus einem beliebigen Werkzeug auf.

## 8. Jeden Morgen das Briefing bekommen

1. Stelle die App hinter HTTPS und installiere sie auf dem Handy, siehe [Handy und Desktop](phone-and-desktop.md).
2. Tippe auf der Seite **Briefing** auf **Benachrichtigungen aktivieren**.
3. Richte den täglichen Zeitgeber ein, siehe [Betrieb → Morgen-Briefing und Prüfregeln](deployment.md#morgen-briefing-und-prüfregeln).

## Ein typischer Tag

1. Das Briefing kommt an. Tippe darauf und lies, was in deinen Live-Projekten dringend ist.
2. Sieh in den *Posteingang* und übernimm oder verwirf, was Agenten vorgeschlagen haben.
3. Wähle ein Projekt, lass den Agenten sein Briefing lesen und arbeiten (unter Windows öffnet der Knopf `>_` ein Terminal für eine Aufgabe).
4. Am Ende protokolliert der Agent, was er getan hat, und hinterlässt eine Notiz zu allem, was man sich merken sollte.
5. Prüfregeln schließen, was sie belegen können. Am nächsten Morgen zeigt das Briefing den neuen Stand.
