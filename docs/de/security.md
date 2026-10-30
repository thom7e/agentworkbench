# Sicherheit

[English](../security.md) · Deutsch

AgentWorkbench ist für eine Person oder ein kleines, vertrauenswürdiges Team gedacht. Diese Seite sagt, was es schützt und was nicht.

## Was vorhanden ist

- **Alles verlangt eine Anmeldung.** Außer `/login`, `/setup`, `/healthz`, den Passkey-Anmelde-Endpunkten, dem Service Worker und statischen Dateien braucht jede Seite eine angemeldete Sitzung. Die API braucht einen Token.
- **Passwörter, Passkeys und Tokens.** Das Admin-Passwort wird mit scrypt gehasht. Passkeys (WebAuthn) werden nur als öffentliche Schlüssel gespeichert, Benutzerverifizierung ist Pflicht, und der Signaturzähler wird geprüft. API-Tokens sind zufällig, werden einmal angezeigt und als SHA-256-Hash gespeichert, eine gestohlene Datenbank verrät sie also nicht.
- **Sitzungen.** Ein signiertes Cookie, `HttpOnly`, `SameSite=Lax`, 30 Tage gültig. Setze hinter HTTPS `AGENTWORKBENCH_COOKIE_SECURE=1`, um es als `Secure` zu markieren.
- **Bremse bei der Anmeldung.** Nach zehn fehlgeschlagenen Passwort-Anmeldungen von einer IP innerhalb von zehn Minuten werden weitere Versuche blockiert. Jeder fehlgeschlagene Versuch wird um eine Sekunde verzögert.
- **Seitenübergreifende Anfragen.** Formular-Posts, deren `Origin`-Header nicht zum Host passt, werden abgelehnt. Zusammen mit `SameSite=Lax`-Cookies deckt das die üblichen CSRF-Fälle ab.
- **Dargestelltes Markdown wird bereinigt.** Notizen und Dokumente werden in HTML umgewandelt und mit einer Erlaubnisliste gesäubert. Skripte, Ereignis-Handler und unbekannte Tags werden entfernt, und nur `http`-, `https`- und `mailto`-Links bleiben erhalten.
- **Lesende Anbindungen.** Der GitHub-Token sollte nur lesen. Der Proxmox-Token nutzt die Rolle `PVEAuditor`. Das Dashboard liest nur.
- **Prüfregeln sind Messfühler, keine Befehle.** Eine Aufgabenprüfung kann nur eine URL abrufen, einen Namen auflösen oder eine TCP-Verbindung öffnen. Sie führt keine Befehle aus und meldet sich nirgends an.
- **Der Link des Desktop-Terminals kann keine Befehle ausführen.** Er trägt nur einen Projekt-Slug und eine Aufgaben-Nummer, beide validiert, und baut daraus einen festen Startauftrag.
- **Die Ersteinrichtung ist einmalig.** `/setup` funktioniert nur, solange kein Passwort existiert.

## Was man wissen sollte

- **Ein Admin, keine Rollen.** Jeder mit dem Passwort oder einem Passkey kann alles ändern, auch Tokens und Einstellungen.
- **API-Tokens haben vollen Zugriff.** Ein Token kann alle Projekte, Notizen und Dokumente lesen und Aufgaben, Notizen und Dokumente schreiben. Er kann keine Einstellungen oder anderen Tokens lesen und erreicht den Adminbereich nicht. Lege pro Agent einen Token an und widerrufe ihn, wenn er nicht mehr gebraucht wird.
- **Geheimnisse in der Datenbank.** Der GitHub-Token, das Proxmox-Token-Geheimnis und der Signaturschlüssel für Push liegen im Klartext in der Tabelle `settings`, weil die App sie verwenden muss. Schütze die Datenbankdatei und ihre Backups und nutze Tokens mit den geringsten Rechten.
- **Kein Geheimnis-Scan.** Notizen und Dokumente werden so gespeichert, wie sie geschrieben wurden. Schreibe keine Zugangsdaten hinein. Filtere beim Import vorhandener Notizen zuerst Geheimnisse heraus.
- **Keine eigene Transportverschlüsselung.** Die App liefert einfaches HTTP. Nutze einen Reverse-Proxy mit HTTPS, wenn sie dein privates Netz verlässt. Passkeys und Push-Benachrichtigungen funktionieren nur über HTTPS.
- **Behalte das Passwort als Ersatz, aber halte es stark.** Bist du aus dem Internet erreichbar, stelle eine Zugriffsschicht davor (zum Beispiel einen Tunnel mit Anmeldung wie Cloudflare Access oder ein VPN). Dann reicht ein verlorenes Passwort allein nicht.
- **Dateirechte der SQLite-Datei.** Mache die Datenbank nur für den Benutzer lesbar, der die App ausführt.

## Ein Problem melden

Wenn du eine Sicherheitslücke findest, eröffne bitte eine private Security-Advisory im GitHub-Repository statt eines öffentlichen Issues. Siehe [SECURITY.md](../../SECURITY.md).
