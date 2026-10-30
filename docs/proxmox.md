# Proxmox integration

English · [Deutsch](de/proxmox.md)

Optional and read-only. When enabled, the dashboard shows which projects run on which container or VM, whether they are up, and their IP address. It never starts, stops or changes anything.

## What you get

- A small **LXC or VM tag** next to every linked project in the project list (amber when it runs, grey when it is stopped; the hover text names guest and node).
- On the project page a **Runs on** card: type and number, name, node, IP, CPU, memory and uptime.
- A **Containers and VMs** section at the bottom of the home page listing every guest of the cluster. Guests without a project have a **Create project** link that pre-fills name and number.
- A **Hide stopped** switch that hides stopped guests and the projects linked to them.
- The API briefing gets a `Runs on:` line, so agents know where a project lives.

## 1. Create a read-only user and token

Run on any node of your cluster (as root):

```bash
pveum user add dashboard@pve --comment "AgentWorkbench, read-only"
pveum acl modify / --users dashboard@pve --roles PVEAuditor
pveum user token add dashboard@pve awb --privsep 0
```

The last command prints the token **value** once. `PVEAuditor` is the built-in role for read-only access. The token ID is `dashboard@pve!awb`.

## 2. Enter it in the settings

**Admin → Settings**:

| Field | Value |
|---|---|
| Proxmox address | `https://<node-ip>:8006` (any node, the cluster API answers for all) |
| Proxmox token ID | `dashboard@pve!awb` |
| Proxmox token secret | the value printed above |
| Verify TLS certificate | Leave off for the default self-signed certificate, turn on if your node has a trusted one |

Save. If the section *Containers and VMs* appears on the home page, it works. If it shows "No data from Proxmox", check address, token ID and secret, and that the dashboard host can reach port 8006.

## 3. Link projects to guests

In **Admin → Projects → (project)** enter the **container or VM number** (for example `137`). Or use **Create project** next to an unlinked guest in the list.

One guest can be linked to several projects, and a project links to one guest.

## How it works

- The dashboard asks `GET /api2/json/cluster/resources?type=vm` and, per guest, the configuration for the IP (`ip=` of `net0` for containers, `ipconfig0` for VMs). For running containers with DHCP it reads the interfaces instead.
- The guest list is cached for 60 seconds, configurations for 10 minutes. If Proxmox is unreachable, the last known data is shown.
- IPs of VMs are only known if they are configured in Proxmox (cloud-init `ipconfig0`). The dashboard does not talk to guest agents.

## Remove the access

```bash
pveum user token remove dashboard@pve awb
pveum user delete dashboard@pve
```

and clear the fields in the settings.
