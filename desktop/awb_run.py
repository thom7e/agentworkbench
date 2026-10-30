"""Handler for agentworkbench://run?project=<slug>&todo=<id> (desktop only).

Opens Windows Terminal in the project folder and starts Claude Code with a fixed prompt that names only the
project and the todo id. Nothing from the link is executed: slug and id are validated, the prompt is a template.

Folder lookup: ~/.claude/awb_paths.json ({"<slug>": "C:\\path"}), else a folder under the projects root whose name
matches the slug (ignoring case, '-' and '_'), else the projects root itself.
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

PATHS = Path.home() / ".claude" / "awb_paths.json"


def projects_root():
    """Root folder of all projects: env AWB_PROJECTS_ROOT, else \"_root\" in awb_paths.json, else ~/projects."""
    mapped = json.loads(PATHS.read_text(encoding="utf-8")) if PATHS.exists() else {}
    return Path(os.environ.get("AWB_PROJECTS_ROOT") or mapped.get("_root") or Path.home() / "projects")


def norm(name):
    return re.sub(r"[-_ ]", "", name).lower()


def project_dir(slug):
    if PATHS.exists():
        mapped = json.loads(PATHS.read_text(encoding="utf-8")).get(slug)
        if mapped and Path(mapped).is_dir():
            return Path(mapped)
    root = projects_root()
    for d in root.iterdir() if root.is_dir() else []:
        if d.is_dir() and norm(d.name) == norm(slug):
            return d
    return root


def build_prompt(slug, todo):
    """Fixed prompt template; returns None for an invalid slug or todo id."""
    if not re.fullmatch(r"[a-z0-9-]{1,64}", slug) or (todo and not re.fullmatch(r"\d{1,9}", todo)):
        return None
    if todo:
        return (f"Bearbeite Todo #{todo} aus dem Dashboard-Projekt {slug}. "
                f"Hole zuerst das Briefing über den Skill agentworkbench und lies das Todo mit dieser ID.")
    return f"Hole das Briefing des Dashboard-Projekts {slug} über den Skill agentworkbench und fasse den Stand kurz zusammen."


def main(url):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    slug, todo = q.get("project", [""])[0], q.get("todo", [""])[0]
    prompt = build_prompt(slug, todo)
    if not prompt:
        sys.exit(1)
    subprocess.Popen(["wt.exe", "-d", str(project_dir(slug)), "powershell.exe", "-NoExit", "-Command", f"claude '{prompt}'"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
