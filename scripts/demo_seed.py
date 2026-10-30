"""Fill an empty AgentWorkbench database with fictional demo data.

    AGENTWORKBENCH_DB=./demo.db python scripts/demo_seed.py
    AGENTWORKBENCH_DB=./demo.db uvicorn app:app

Signs in with the password printed at the end. Refuses to touch a database that already has projects.
"""
import json
import sys
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import auth  # noqa: E402
import db  # noqa: E402
import settings  # noqa: E402

PASSWORD = "demo-password-123"
NOW = datetime.now()


def ts(days_ago=0, hour=9):
    return (NOW - timedelta(days=days_ago)).replace(hour=hour, minute=15).strftime("%Y-%m-%d %H:%M")


AREAS = ["Customer sites", "Internal tools", "Infrastructure", "Side projects"]

# slug, name, area, status, deploy, stack, summary
PROJECTS = [
    ("bakery-site", "Hofmann Bakery Website", "Customer sites", "aktiv", "Shared hosting", "PHP, MariaDB",
     "Relaunch of the bakery site with online pre-orders for the weekend."),
    ("dental-booking", "Dental Practice Booking", "Customer sites", "aktiv", "VPS", "Django, PostgreSQL",
     "Appointment requests with e-mail confirmation and a small admin area for the front desk."),
    ("choir-tickets", "City Choir Tickets", "Customer sites", "aktiv", "Docker on a VPS", "FastAPI, SQLite",
     "Ticket sales and seat map for the winter concerts."),
    ("timesheets", "Timesheets", "Internal tools", "aktiv", "Docker on the NAS", "FastAPI, SQLite",
     "Track hours per project and export monthly invoices as PDF."),
    ("invoice-bot", "Invoice Bot", "Internal tools", "aktiv", "systemd timer", "Python",
     "Reads supplier invoices from a mailbox, files them and posts a summary to the team chat."),
    ("team-wiki", "Team Wiki", "Internal tools", "pause", "Docker on the NAS", "DokuWiki",
     "Handbook for onboarding and office routines."),
    ("nas-backup", "NAS Backup", "Infrastructure", "aktiv", "Synology + Backblaze B2", "Hyper Backup",
     "Nightly backup of shares to the cloud, monthly restore test."),
    ("home-assistant", "Home Assistant", "Infrastructure", "aktiv", "Raspberry Pi 5", "Home Assistant OS",
     "Heating schedule, presence detection and energy dashboard."),
    ("vpn", "WireGuard VPN", "Infrastructure", "aktiv", "VPS", "WireGuard",
     "Access to the office network from anywhere."),
    ("recipe-box", "Recipe Box", "Side projects", "aktiv", "Static hosting", "Static site generator",
     "Personal recipe collection with search."),
    ("sudoku", "Sudoku Solver", "Side projects", "pause", "", "Python", "Backtracking solver with a tiny CLI."),
    ("old-blog", "Old Blog", "Side projects", "archiv", "", "Jekyll", "Archived. Content moved to the new site."),
]

# slug, text, prio, kind, done_days_ago (None = open)
TODOS = [
    ("bakery-site", "Order form: limit pre-orders to 40 per day", 1, "todo", None),
    ("bakery-site", "Compress hero images (largest SEO win)", 2, "todo", None),
    ("bakery-site", "Add opening hours to the footer", 3, "todo", None),
    ("bakery-site", "Set up the contact form with spam protection", 2, "todo", 3),
    ("bakery-site", "Seasonal landing page for the Christmas stollen", 3, "idee", None),
    ("dental-booking", "Send a reminder e-mail 24 hours before the appointment", 1, "todo", None),
    ("dental-booking", "Let patients cancel through a link in the e-mail", 2, "todo", None),
    ("dental-booking", "Privacy policy: mention appointment e-mails", 2, "todo", None),
    ("choir-tickets", "Fix seat map on small phones", 2, "todo", None),
    ("choir-tickets", "Box office mode: print tickets as PDF", 2, "todo", None),
    ("choir-tickets", "Discount code for choir members", 3, "idee", None),
    ("timesheets", "Import last year's hours from the old spreadsheet", 2, "todo", None),
    ("timesheets", "Monthly PDF export with company logo", 3, "todo", 5),
    ("invoice-bot", "Handle invoices that arrive as ZIP attachments", 2, "todo", None),
    ("invoice-bot", "Weekly digest instead of a message per invoice", 3, "idee", None),
    ("team-wiki", "Review the onboarding checklist", 3, "todo", None),
    ("nas-backup", "Restore test: pick three random folders and compare checksums", 1, "todo", None),
    ("nas-backup", "Replace the old USB disk used for the second copy", 2, "todo", None),
    ("home-assistant", "Tune the heating curve before the first frost", 1, "todo", None),
    ("home-assistant", "Add the energy sensor of the heat pump", 2, "todo", None),
    ("vpn", "Rotate peer keys", 2, "todo", None),
    ("recipe-box", "Tag recipes by season", 3, "idee", None),
    ("recipe-box", "Print stylesheet for recipe pages", 3, "todo", None),
]

# agent-created, unseen: slug, text, prio
INBOX = [
    ("dental-booking", "Time zone bug: appointments after 23:00 are stored one day earlier", 1),
    ("timesheets", "Dependency update: three packages have security fixes", 2),
    ("invoice-bot", "Log file grows without rotation, add logrotate", 3),
]

# slug, text, author, pinned, days_ago
NOTES = [
    ("bakery-site", "**Decision:** no online payment in the first release. Customers pay when they pick up the order. "
                    "Reason: the owner does not want to deal with payment fees and refunds.", "user", 1, 12),
    ("bakery-site", "The shared hosting plan limits PHP to 128 MB memory. Image resizing must happen at upload, not on request.",
     "agent", 0, 4),
    ("nas-backup", "Restore tests: use the `restore-test` share, never restore into the original folder.\n\n"
                   "Last full test: **passed**, 3 of 3 folders identical.", "agent", 1, 6),
    ("home-assistant", "The heating automation reads the outdoor temperature from the weather integration. "
                       "If that fails, it falls back to the last known value for six hours.", "user", 1, 9),
    ("dental-booking", "The front desk wants to see the day list sorted by time, not by name.", "user", 0, 2),
]

DOCS = [
    ("nas-backup", "Backup runbook",
     "# Backup runbook\n\n## Schedule\n\n| Job | When | Target |\n|---|---|---|\n| Shares | daily 02:00 | Backblaze B2 |\n"
     "| System config | weekly Sunday 03:00 | Second NAS |\n\n## Restore a folder\n\n1. Open **Hyper Backup**\n2. Pick the version\n"
     "3. Restore into `restore-test`\n4. Compare checksums:\n\n```bash\nsha256sum -c checksums.txt\n```\n\n> Never restore into the original folder."),
    ("home-assistant", "Heating schedule",
     "# Heating schedule\n\n- Weekdays: 06:00 to 22:00, 21 °C\n- Weekends: 08:00 to 23:00, 21 °C\n- Night: 17 °C\n\n"
     "The schedule lives in `schedules.yaml`. Change it there, not in the UI."),
    ("bakery-site", "Launch checklist",
     "# Launch checklist\n\n- [x] Domain and DNS\n- [x] Contact form\n- [ ] Pre-order form\n- [ ] Privacy policy and imprint\n- [ ] Redirects from the old site"),
]

ACTIVITY = [
    ("bakery-site", "Contact form live, spam protection tested", 3),
    ("nas-backup", "Monthly restore test passed", 6),
    ("timesheets", "PDF export now includes the company logo", 5),
    ("home-assistant", "Added the weather fallback for the heating automation", 9),
    ("dental-booking", "Reminder e-mails drafted, waiting for the privacy text", 2),
    ("invoice-bot", "Parser handles invoices with several pages", 11),
    ("choir-tickets", "Seat map renders on tablets", 15),
    ("vpn", "Added a second peer for the laptop", 40),
]


def main():
    db.init()
    with closing(db.db()) as con:
        if con.execute("SELECT COUNT(*) FROM projects").fetchone()[0]:
            sys.exit("This database already has projects. Use an empty database for the demo.")
        for i, (slug, name, area, status, deploy, stack, summary) in enumerate(PROJECTS):
            con.execute("INSERT INTO projects(slug,name,area,status,deploy,stack,summary,sort) VALUES(?,?,?,?,?,?,?,?)",
                        (slug, name, area, status, deploy, stack, summary, i))
        con.execute("UPDATE projects SET live=1 WHERE slug IN ('bakery-site', 'dental-booking', 'choir-tickets')")
        for slug, text, prio, kind, done in TODOS:
            con.execute("INSERT INTO todos(project,text,kind,prio,done,created,done_at) VALUES(?,?,?,?,?,?,?)",
                        (slug, text, kind, prio, 0 if done is None else 1, ts(20), None if done is None else ts(done)))
        for slug, text, prio in INBOX:
            con.execute("INSERT INTO todos(project,text,kind,prio,created,source,seen) VALUES(?,?,'todo',?,?,'agent',0)",
                        (slug, text, prio, ts(0, 8)))
        for slug, text, author, pinned, days in NOTES:
            con.execute("INSERT INTO notes(project,text,author,pinned,created) VALUES(?,?,?,?,?)",
                        (slug, text, author, pinned, ts(days)))
        for slug, title, body in DOCS:
            con.execute("INSERT INTO docs(project,title,body,created,updated) VALUES(?,?,?,?,?)",
                        (slug, title, body, ts(30), ts(7)))
        for slug, text, days in ACTIVITY:
            con.execute("INSERT INTO activity(project,text,ts) VALUES(?,?,?)", (slug, text, ts(days, 16)))
        con.commit()
    settings.put("site_title", "AgentWorkbench")
    settings.put("language", "en")
    settings.put("owner_name", "Alex")
    settings.put("areas", json.dumps(AREAS))
    settings.put("admin_hash", auth.hash_password(PASSWORD))
    print(f"Demo data created in {db.DB_PATH}\nSign in with the password: {PASSWORD}")


if __name__ == "__main__":
    main()
