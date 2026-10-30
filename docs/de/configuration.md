# Konfiguration

[English](../configuration.md) · Deutsch

Fast alles wird im Adminbereich eingestellt. Einige Werte kommen aus der Umgebung, weil sie bekannt sein müssen, bevor die Datenbank geöffnet wird.

## Umgebungsvariablen

| Variable | Standard | Zweck |
|---|---|---|
| `AGENTWORKBENCH_DB` | `./dashboard.db` (Docker: `/data/dashboard.db`) | Pfad der SQLite-Datei |
| `AGENTWORKBENCH_COOKIE_SECURE` | `0` | Auf `1` setzen, wenn du die App über HTTPS auslieferst, damit das Sitzungs-Cookie als `Secure` markiert wird |
| `AGENTWORKBENCH_TOKEN` | leer | Optionaler statischer API-Token. Im Adminbereich angelegte Tokens sind vorzuziehen, weil sie widerrufbar sind |
| `GITHUB_TOKEN` | leer | Ersatz, wenn in den Einstellungen kein GitHub-Token gespeichert ist |

## Verwaltung → Einstellungen

| Einstellung | Bedeutung |
|---|---|
| **Titel der Seite** | Steht in der Kopfzeile und im Browser-Tab |
| **Sprache** | `de` oder `en`. Gilt für die ganze Oberfläche und das Briefing |
| **Gruppen** | Eine Gruppe pro Zeile, in der Reihenfolge, in der sie auf der Startseite erscheinen. Ein Projekt, dessen Gruppe nicht in dieser Liste steht, erscheint in der ersten Gruppe |
| **Ruhend nach (Tagen)** | Ein Projekt ohne offene Aufgaben und ohne Aktivität oder Push seit so vielen Tagen wandert in den eingeklappten Bereich *Ruhend* seiner Gruppe. Standard 90 |
| **Standard-Sortierung** | Reihenfolge der Projekte in einer Gruppe: *letzte Aktivität* (neueste zuerst, nach dem späteren von letztem Protokolleintrag und letztem GitHub-Push) oder *offene Aufgaben* |
| **GitHub-Konto oder -Organisation** | Benutzer oder Organisation, deren Repositories gelistet werden |
| **GitHub-Token (nur lesend)** | Lesender Token, siehe [Erste Schritte](getting-started.md#optional-github). Lass das Feld leer, um den gespeicherten Token zu behalten |
| **Dein Vorname** | Optional. Wird in der Begrüßung des Morgen-Briefings verwendet |
| **Kontakt für Push-Nachrichten** | Eine `mailto:`- oder `https`-Adresse, die Push-Diensten als Absenderkontakt gesendet wird. Apple verlangt einen gültigen Wert, damit Web-Push ankommt |
| **Proxmox-Adresse, Token-ID, Token-Secret, TLS prüfen** | Optional, siehe [Proxmox-Anbindung](proxmox.md) |

Die Einstellungen liegen in der Tabelle `settings` der Datenbank. Der GitHub-Token und das Proxmox-Geheimnis liegen dort im Klartext, schütze die Datenbankdatei also wie jedes andere Geheimnis.

## Projektfelder

| Feld | Bedeutung |
|---|---|
| Name, Slug | Der Slug ist der stabile Schlüssel in URLs und API. Er wird beim Anlegen aus dem Namen gebildet und lässt sich danach nicht mehr ändern |
| Status | `aktiv`, `pause` (pausiert), `archiv` (archiviert). Pausierte und archivierte Projekte erscheinen nicht im Briefing |
| Live | Setze den Haken für Projekte, die produktiv laufen oder beim Kunden sind. Sie bekommen einen eigenen Abschnitt im Briefing und eine Lampe im Seitenmenü, siehe [Briefing und Prüfregeln](briefing-and-checks.md#der-live-schalter) |
| Gruppe | Eine der Gruppen aus den Einstellungen |
| Hosting, Stack | Freier Text, steht auf der Projektseite |
| Zusammenfassung | Ein bis zwei Sätze, stehen unter dem Titel und in der Suche |
| GitHub-Repo | `owner/name`. Schaltet den Git-Bereich und den Zeitpunkt des letzten Pushs frei |
| Wiki-Adresse | Link, der auf der Projektseite erscheint |
| Notizen | Links zu externen Notizen (Spezifikationen, Wiki-Seiten), eine Webadresse pro Zeile |
| Container- oder VM-Nummer | Verknüpft das Projekt mit einem Proxmox-Gast, siehe [Proxmox-Anbindung](proxmox.md) |

## Aussehen

Ein Design mit hellem und dunklem Thema, das dem System folgt. Farben, Schriften und das Seitenmenü liegen in `static/op.css`; ändere die Variablen am Anfang dieser Datei, um die App umzufärben. Struktur und gemeinsame Bausteine stehen in `static/style.css`.

## Daten

| Aktion | Wo |
|---|---|
| Alles als JSON herunterladen | **Verwaltung → Daten → Export** (Projekte, Aufgaben, Verlauf, Notizen, Dokumente) |
| Ein JSON-Backup wiederherstellen | **Verwaltung → Daten → Import → JSON-Backup wiederherstellen**. Projekte mit gleichem Slug werden samt ihren Aufgaben, Notizen, Dokumenten und ihrem Verlauf ersetzt. Alles andere wird hinzugefügt |
| Markdown importieren | **Verwaltung → Daten → Markdown importieren** |
| Alle Notizen als Markdown | `GET /export/notes.md` |
| Alle offenen Aufgaben als Markdown | `GET /export/todo.md` |

Das JSON-Backup enthält keine Einstellungen, Tokens oder das Admin-Passwort. Für ein vollständiges Backup kopiere die Datenbankdatei, siehe [Betrieb → Backups](deployment.md#backups).
