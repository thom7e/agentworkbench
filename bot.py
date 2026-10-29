"""Telegram bot (long polling): choose per project whether it shows up in detail in the morning digest.

Commands: /projekte (toggle buttons), /briefing (send the digest now), /hilfe.
Only the chat configured as TG_CHAT_ID is served. Credentials come from the environment or DIGEST_ENV.
"""
import json
import os
import time
import urllib.request
from contextlib import closing

import digest
from db import db

HELP = ("/projekte – Projekte ausführlich ins Briefing aufnehmen oder unter „Sonst offen“ schieben\n"
        "/briefing – Briefing jetzt senden")


def api(method, **params):
    token = os.environ["TG_BOT_TOKEN"]
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=json.dumps(params).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["result"]


def project_rows(con):
    marks = ",".join("?" * len(digest.HIDDEN))
    return con.execute(
        f"SELECT slug, name, live FROM projects WHERE status NOT IN ({marks}) AND (live=1 OR EXISTS "
        f"(SELECT 1 FROM todos t WHERE t.project=projects.slug AND t.done=0 AND t.kind='todo' AND t.prio<=2)) "
        f"ORDER BY live DESC, name COLLATE NOCASE", digest.HIDDEN).fetchall()


def keyboard(con):
    return {"inline_keyboard": [[{"text": f"{'✅' if r['live'] else '▫️'} {r['name']}", "callback_data": f"t:{r['slug']}"}]
                                for r in project_rows(con)]}


def toggle(con, slug):
    con.execute("UPDATE projects SET live=1-live WHERE slug=?", (slug,))
    con.commit()


def handle(update, chat):
    msg = update.get("message")
    cb = update.get("callback_query")
    if msg and str(msg["chat"]["id"]) == chat:
        cmd = (msg.get("text") or "").split("@")[0].strip().lower()
        if cmd == "/projekte":
            with closing(db()) as con:
                api("sendMessage", chat_id=chat, reply_markup=keyboard(con),
                    text="✅ = ausführlich im Briefing, ▫️ = nur unter „Sonst offen“. Tippen schaltet um.")
        elif cmd == "/briefing":
            with closing(db()) as con:
                digest.send(digest.build_digest(con, url=os.environ.get("DASHBOARD_URL", "")))
        else:
            api("sendMessage", chat_id=chat, text=HELP)
    elif cb and str(cb["message"]["chat"]["id"]) == chat and cb["data"].startswith("t:"):
        with closing(db()) as con:
            toggle(con, cb["data"][2:])
            api("editMessageReplyMarkup", chat_id=chat, message_id=cb["message"]["message_id"], reply_markup=keyboard(con))
        api("answerCallbackQuery", callback_query_id=cb["id"], text="Umgeschaltet")


def main():
    digest.load_env()
    chat = os.environ["TG_CHAT_ID"]
    api("setMyCommands", commands=[{"command": "projekte", "description": "Projekte im Briefing wählen"},
                                   {"command": "briefing", "description": "Briefing jetzt senden"}])
    offset = 0
    while True:
        try:
            for u in api("getUpdates", offset=offset, timeout=50):
                offset = u["update_id"] + 1
                handle(u, chat)
        except Exception as e:
            print("bot error:", e, flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
