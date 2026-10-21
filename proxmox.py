import json
import re
import ssl
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import settings

LIST_TTL = 60
CONFIG_TTL = 600
_cache = {}


def enabled():
    return bool(settings.get("proxmox_url") and settings.get("proxmox_token_id") and settings.get("proxmox_token_secret"))


def _request(path):
    ctx = ssl.create_default_context() if settings.get("proxmox_verify_tls") == "1" else ssl._create_unverified_context()
    req = urllib.request.Request(
        settings.get("proxmox_url").rstrip("/") + "/api2/json" + path,
        headers={"Authorization": f"PVEAPIToken={settings.get('proxmox_token_id')}={settings.get('proxmox_token_secret')}"},
    )
    with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))["data"]


def _get(path, ttl):
    hit = _cache.get(path)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    try:
        data = _request(path)
    except Exception:
        return hit[1] if hit else None
    _cache[path] = (time.time(), data)
    return data


def _ip(guest):
    base = f"/nodes/{guest['node']}/{guest['type']}/{guest['vmid']}"
    cfg = _get(base + "/config", CONFIG_TTL) or {}
    for key in ("net0", "ipconfig0"):
        m = re.search(r"\bip=(\d+\.\d+\.\d+\.\d+)", cfg.get(key, ""))
        if m:
            return m.group(1)
    if guest["type"] == "lxc" and guest["status"] == "running":
        for iface in _get(base + "/interfaces", LIST_TTL) or []:
            m = re.match(r"(\d+\.\d+\.\d+\.\d+)", iface.get("inet", ""))
            if m and iface.get("name") != "lo":
                return m.group(1)
    return ""


def guests():
    if not enabled():
        return []
    rows = _get("/cluster/resources?type=vm", LIST_TTL) or []
    out = [
        {"vmid": r["vmid"], "name": r.get("name", ""), "node": r["node"], "type": r["type"],
         "status": r.get("status", "unknown"), "cpu": r.get("cpu", 0), "mem": r.get("mem", 0),
         "maxmem": r.get("maxmem", 0), "uptime": r.get("uptime", 0), "ip": ""}
        for r in rows if not r.get("template")
    ]
    with ThreadPoolExecutor(8) as pool:
        for g, ip in zip(out, pool.map(_ip, out)):
            g["ip"] = ip
    return sorted(out, key=lambda g: g["vmid"])


def by_vmid():
    return {g["vmid"]: g for g in guests()}
