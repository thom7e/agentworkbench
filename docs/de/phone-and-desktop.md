# Handy und Desktop

[English](../phone-and-desktop.md) · Deutsch

## Die Handy-App

AgentWorkbench ist eine Progressive Web App. Sie öffnet sich im Vollbild und fühlt sich wie eine App an, ohne App-Store.

**Installieren:** Öffne die Seite in Safari (iPhone) oder Chrome (Android) und wähle **Teilen → Zum Home-Bildschirm**. Stelle die Seite hinter HTTPS, wenn du sie außerhalb deines Heimnetzes öffnest, siehe [Betrieb](deployment.md#https-und-reverse-proxy).

**Was du auf dem Handy bekommst**

| Funktion | Wie es funktioniert |
|---|---|
| Tab-Leiste | *Heute*, *Projekte*, *Briefing* und *Mehr* unten. *Heute* und *Projekte* sind zwei Ansichten der Startseite, die sofort wechseln |
| Schnell-Eintrag | Der runde **+**-Knopf. Gib eine Aufgabe oder Idee ein (zum Diktieren die Mikrofontaste der Tastatur), wähle Projekt und Priorität, speichere. Ohne Verbindung bleibt der Eintrag auf dem Handy und wird gesendet, sobald du wieder online bist |
| Wischen zum Abhaken | Eine Aufgabenkarte nach links wischen |
| Ziehen zum Aktualisieren | Oben auf einer Seite nach unten ziehen |
| Offline lesen | Seiten, die du geöffnet hast, bleiben erhalten. Beim Abmelden werden sie gelöscht |
| Benachrichtigungen | Siehe unten |

**Updates:** Die App-Dateien tragen eine Versionsnummer, eine neue Version lädt sich also beim nächsten Öffnen von selbst. Sieht etwas alt aus, schließe die App ganz und öffne sie neu.

## Benachrichtigungen

Das Morgen-Briefing und die Hinweise „automatisch abgehakt“ kommen als Web-Push-Benachrichtigungen.

1. Öffne die Seite **Briefing** in der installierten App und tippe auf **Benachrichtigungen aktivieren**. Erlaube sie, wenn das Handy fragt. Eine Testbenachrichtigung kommt sofort.
2. **iPhone:** Web-Push funktioniert ab iOS 16.4 und **nur für die App auf dem Home-Bildschirm**, nicht im Browser-Tab.
3. Ein Tipp auf eine Benachrichtigung öffnet die Briefing-Seite.

Benachrichtigungen brauchen HTTPS. Apple verlangt einen gültigen Absender-Kontakt, trage ihn unter **Verwaltung → Einstellungen → Kontakt für Push-Nachrichten** ein (eine `mailto:`-Adresse, die dir gehört). Der Server erzeugt beim ersten Gebrauch einen eigenen VAPID-Schlüssel und speichert ihn in der Datenbank.

Welche Geräte Benachrichtigungen bekommen, entscheidet, wer die Glocke getippt hat: Jedes Gerät meldet sich selbst an. Ein Gerät, das sich abgemeldet hat oder zurückgesetzt wurde, wird automatisch entfernt.

## Passkeys

Ein Passkey meldet dich mit Face ID, Touch ID oder Windows Hello an, statt das Passwort zu tippen. Er lässt sich nicht abfischen und nicht erraten.

- **Einen anlegen:** **Verwaltung → Einstellungen → Passkeys**, einen Namen eingeben (zum Beispiel *iPhone*), **Passkey hinzufügen** tippen und am Gerät bestätigen. Passkeys brauchen HTTPS (oder `localhost`).
- **Benutzen:** Wähle auf der Anmeldeseite **Mit Passkey anmelden**.
- **Empfohlen:** ein Passkey pro Gerät, das du nutzt, und insgesamt mindestens zwei. Das Passwort bleibt als Ersatz.
- **Einen entfernen:** Die Liste unter *Passkeys* hat je Gerät einen Link *Entfernen*.

Der Passkey ist an die Adresse gebunden, auf der du ihn angelegt hast. Ziehst du die Seite auf eine neue Domain um, lege die Passkeys neu an.

## Das Desktop-Terminal (optional, Windows)

Am Desktop erscheint neben jeder Aufgabe ein kleiner Knopf `>_` und im Projektkopf ein Chip *Terminal*. Ein Klick öffnet **Windows Terminal im Projektordner und startet deinen KI-Agenten mit der Aufgabe als Startauftrag**. Er wird nur in Desktop-Browsern gezeigt, nie auf Handys und Tablets.

**So funktioniert es.** Der Knopf ist ein Link mit eigenem Schema, `agentworkbench://run?project=<slug>&todo=<id>`. Ein kleiner Handler, der für deinen Windows-Benutzer registriert ist, nimmt ihn entgegen. Der Handler akzeptiert nur einen gültigen Projekt-Slug und eine numerische Aufgaben-Nummer und baut daraus einen **festen Startauftrag** (*bearbeite Aufgabe #12 des Projekts X, lies zuerst das Briefing*). Nichts aus dem Link wird je als Befehl ausgeführt, und nichts wird über das Netz gesendet.

**Einrichten**

1. Stelle sicher, dass `wt.exe` (Windows Terminal) und dein Agenten-Befehl (`claude`) im `PATH` liegen.
2. Registriere den Handler für deinen Benutzer (keine Adminrechte nötig):

   ```powershell
   powershell -File desktop\install_windows.ps1
   ```

3. Sage dem Handler, wo deine Projekte liegen. Setze entweder die Umgebungsvariable `AWB_PROJECTS_ROOT` (Standard `~/projects`) oder lege `~/.claude/awb_paths.json` an:

   ```json
   {"_root": "C:\\Users\\du\\Documents\\projects", "website": "C:\\work\\website-v2"}
   ```

   In `_root` wird nach einem Ordner gesucht, der wie der Projekt-Slug heißt (Groß-/Kleinschreibung, `-` und `_` egal). Einzelne Projekte lassen sich per Slug auf einen beliebigen Ordner abbilden.

4. Der Agent findet seine Zugangsdaten wie in [Mit Agenten arbeiten](agents.md#claude-code) beschrieben.

Für einen anderen Agenten oder ein anderes Terminal bearbeite die letzte Zeile von `desktop/awb_run.py`.
