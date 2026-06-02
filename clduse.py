#!/usr/bin/env python3
import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db, get_today
from config import DB_PATH


def cmd_default():
    from display import show_dashboard
    show_dashboard()


def cmd_log(task):
    from categorize import categorize
    init_db()
    sessions = get_today()
    if not sessions:
        print("No sessions today to label.")
        return
    latest = sessions[0]
    cat = categorize(task)
    with sqlite3.connect(DB_PATH) as c:
        c.execute("UPDATE sessions SET task=?, category=? WHERE id=?",
                  (task, cat, latest["id"]))
    print(f"Labeled: [{cat}] {task}  (session {latest['id'][:12]})")


def cmd_today():
    from display import show_today
    show_today()


def cmd_week():
    from analysis import show_week
    show_week()


def cmd_sync():
    from gas_sync import sync_sessions
    sync_sessions()


def cmd_resync(args):
    from gas_sync import resync_sessions
    scope = args[0] if args else "today"
    if scope not in ("today", "week", "month"):
        print("Usage: clduse resync [today|week|month]")
        sys.exit(1)
    resync_sessions(scope)


def cmd_daemon(args):
    import daemon as d
    sub = args[0] if args else "status"
    if sub == "start":
        d.cmd_start()
    elif sub == "stop":
        d.cmd_stop()
    else:
        d.cmd_status()


def cmd_scan():
    from reader import scan_sessions
    from db import insert_session
    init_db()
    sessions = scan_sessions()
    for s in sessions:
        insert_session(s)
    print(f"Scanned and inserted {len(sessions)} sessions.")


def main():
    args = sys.argv[1:]
    if not args:
        cmd_default()
        return

    cmd  = args[0]
    rest = args[1:]

    if cmd == "log":
        if not rest:
            print('Usage: clduse log "task description"')
            sys.exit(1)
        cmd_log(" ".join(rest))
    elif cmd == "today":
        cmd_today()
    elif cmd == "week":
        cmd_week()
    elif cmd == "sync":
        cmd_sync()
    elif cmd == "resync":
        cmd_resync(rest)
    elif cmd == "daemon":
        cmd_daemon(rest)
    elif cmd == "scan":
        cmd_scan()
    elif cmd == "sync" and rest == ["--test"]:
        cmd_sync()
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: log <task> | today | week | sync | resync [today|week|month] | daemon start/stop/status | scan")
        sys.exit(1)


if __name__ == "__main__":
    main()
