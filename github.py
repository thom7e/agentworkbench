import json
import os
import time
import urllib.request

import settings

TTL = 900
_cache = {}


def _token():
    return settings.get("github_token") or os.environ.get("GITHUB_TOKEN", "")


def _get(path, raw=False):
    key = (path, raw, _token())
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    headers = {
        "Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json",
        "User-Agent": "agentworkbench",
    }
    if _token():
        headers["Authorization"] = f"Bearer {_token()}"
    try:
        with urllib.request.urlopen(urllib.request.Request("https://api.github.com" + path, headers=headers),
                                    timeout=10) as r:
            body = r.read().decode("utf-8")
        data = body if raw else json.loads(body)
    except Exception:
        return hit[1] if hit else None
    _cache[key] = (time.time(), data)
    return data


def enabled():
    return bool(settings.get("github_owner") and _token())


def list_repos():
    owner = settings.get("github_owner")
    if not enabled():
        return []
    repos = _get("/user/repos?per_page=100&sort=pushed&affiliation=owner") or []
    return [r for r in repos if r["owner"]["login"].lower() == owner.lower()]


def pushed_map():
    return {r["full_name"].lower(): r["pushed_at"] for r in list_repos()}


def repo_detail(full_name):
    if not enabled():
        return None
    info = _get(f"/repos/{full_name}")
    if not info:
        return None
    branches = _get(f"/repos/{full_name}/branches?per_page=30") or []
    commits = _get(f"/repos/{full_name}/commits?per_page=10") or []
    readme = _get(f"/repos/{full_name}/readme", raw=True) or ""
    return {
        "url": info["html_url"],
        "private": info["private"],
        "description": info.get("description") or "",
        "default_branch": info["default_branch"],
        "branches": [b["name"] for b in branches],
        "commits": [
            {
                "sha": c["sha"][:7],
                "url": c["html_url"],
                "msg": c["commit"]["message"].split("\n")[0],
                "date": c["commit"]["author"]["date"][:10],
            }
            for c in commits
        ],
        "readme": readme_excerpt(readme),
    }


def readme_excerpt(md, limit=700):
    out = []
    for block in md.replace("\r", "").split("\n\n"):
        b = block.strip()
        if not b or b.startswith(("#", "[![", "![", "<", "|", "```", "---", "===")):
            continue
        out.append(" ".join(b.split()))
        if sum(map(len, out)) > limit:
            break
    return "\n\n".join(out)[:limit]


def open_prs():
    owner = settings.get("github_owner")
    if not enabled():
        return []
    res = _get(f"/search/issues?q=is:pr+is:open+user:{owner}+archived:false&sort=created&order=desc&per_page=30")
    return [
        {
            "repo": i["repository_url"].split("/repos/")[1],
            "title": i["title"],
            "url": i["html_url"],
            "author": i["user"]["login"],
            "created": i["created_at"][:10],
            "draft": bool(i.get("draft")),
        }
        for i in (res or {}).get("items", [])
    ]
