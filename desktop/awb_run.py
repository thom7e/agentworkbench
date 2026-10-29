"""Handler for agentworkbench://run?project=<slug>&todo=<id> (desktop only).

Opens Windows Terminal in the project folder and starts Claude Code with a fixed prompt that names only the
project and the todo id. Nothing from the link is executed: slug and id are validated, the prompt is a template.

Folder lookup: ~/.claude/awb_paths.json ({"<slug>": "C:\\path"}), else a folder under the projects root whose name
matches the slug (ignoring case, '-' and '_'), else the projects root itself.
"""
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path.home() / "Documents" / "github_aktuell"
PATHS = Path.home() / ".claude" / "awb_paths.json"


def norm(name):
    return re.sub(r"[-_ ]", "", name).lower()


def project_dir(slug):
    if PATHS.exists():
        mapped = json.loads(PATHS.read_text(encoding="utf-8")).get(slug)
        if mapped and Path(mapped).is_dir():
            return Path(mapped)
    for d in ROOT.iterdir() if ROOT.is_dir() else []:
        if d.is_dir() and norm(d.name) == norm(slug):
            return d
    return ROOT


def main(url):
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    slug, todo = q.get("project", [""])[0], q.get("todo", [""])[0]
    if not re.fullmatch(r"[a-z0-9-]{1,64}", slug) or not re.fullmatch(r"\d{1,9}", todo):
        sys.exit(1)
    prompt = (f"Bearbeite Todo #{todo} aus dem Dashboard-Projekt {slug}. "
              f"Hole zuerst das Briefing über den Skill agentworkbench und lies das Todo mit dieser ID.")
    subprocess.Popen(["wt.exe", "-d", str(project_dir(slug)), "powershell.exe", "-NoExit", "-Command", f"claude '{prompt}'"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
