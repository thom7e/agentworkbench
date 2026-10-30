# Proxmox-Anbindung

[English](../proxmox.md) · Deutsch

Optional und nur lesend. Ist sie aktiv, zeigt das Dashboard, welche Projekte auf welchem Container oder welcher VM laufen, ob sie laufen und welche IP-Adresse sie haben. Es startet, stoppt oder ändert nie etwas.

## Was du bekommst

- Ein kleines **LXC- oder VM-Kennzeichen** neben jedem verknüpften Projekt in der Projektliste (bernsteinfarben, wenn es läuft, grau, wenn es gestoppt ist; der Hover-Text nennt Gast und Node).
- Auf der Projektseite eine Karte **Läuft auf**: Typ und Nummer, Name, Node, IP, CPU, Speicher und Laufzeit.
- Ein Bereich **Container und VMs** unten auf der Startseite, der jeden Gast des Clusters listet. Gäste ohne Projekt haben einen Link **Projekt anlegen**, der Name und Nummer vorbelegt.
- Ein Schalter **Gestoppte ausblenden**, der gestoppte Gäste und die mit ihnen verknüpften Projekte ausblendet.
- Das API-Briefing bekommt eine Zeile `Runs on:`, damit Agenten wissen, wo ein Projekt lebt.

## 1. Lesenden Benutzer und Token anlegen

Auf einem beliebigen Node deines Clusters ausführen (als root):

```bash
pveum user add dashboard@pve --comment "AgentWorkbench, nur lesen"
pveum acl modify / --users dashboard@pve --roles PVEAuditor
pveum user token add dashboard@pve awb --privsep 0
```

Der letzte Befehl gibt den Token-**Wert** einmal aus. `PVEAuditor` ist die eingebaute Rolle für reinen Lesezugriff. Die Token-ID ist `dashboard@pve!awb`.

## 2. In den Einstellungen eintragen

**Verwaltung → Einstellungen**:

| Feld | Wert |
|---|---|
| Proxmox-Adresse | `https://<node-ip>:8006` (ein beliebiger Node, die Cluster-API antwortet für alle) |
| Proxmox-Token-ID | `dashboard@pve!awb` |
| Proxmox-Token-Secret | der oben ausgegebene Wert |
| TLS-Zertifikat prüfen | Für das selbstsignierte Standardzertifikat aus lassen, einschalten, wenn dein Node ein vertrauenswürdiges hat |

Speichern. Erscheint der Bereich *Container und VMs* auf der Startseite, funktioniert es. Steht dort „Keine Daten von Proxmox“, prüfe Adresse, Token-ID und Geheimnis und ob der Dashboard-Host Port 8006 erreicht.

## 3. Projekte mit Gästen verknüpfen

Trage unter **Verwaltung → Projekte → (Projekt)** die **Container- oder VM-Nummer** ein (zum Beispiel `137`). Oder nutze **Projekt anlegen** neben einem nicht verknüpften Gast in der Liste.

Ein Gast kann mit mehreren Projekten verknüpft sein, ein Projekt verknüpft sich mit einem Gast.

## So funktioniert es

- Das Dashboard fragt `GET /api2/json/cluster/resources?type=vm` und je Gast die Konfiguration für die IP (`ip=` von `net0` bei Containern, `ipconfig0` bei VMs). Bei laufenden Containern mit DHCP liest es stattdessen die Schnittstellen.
- Die Gästeliste wird 60 Sekunden zwischengespeichert, Konfigurationen 10 Minuten. Ist Proxmox nicht erreichbar, werden die zuletzt bekannten Daten gezeigt.
- IPs von VMs sind nur bekannt, wenn sie in Proxmox konfiguriert sind (cloud-init `ipconfig0`). Das Dashboard spricht nicht mit Gast-Agenten.

## Den Zugang entfernen

```bash
pveum user token remove dashboard@pve awb
pveum user delete dashboard@pve
```

und die Felder in den Einstellungen leeren.
