import os
import sys
import time
import json
import signal
import subprocess
import uuid
from datetime import datetime
from config import CLD_DIR

PID_FILE   = os.path.join(CLD_DIR, "daemon.pid")
LOG_FILE   = os.path.join(CLD_DIR, "daemon.log")
STATE_FILE = os.path.join(CLD_DIR, "daemon.state")

SAFARI_SCRIPT = '''
tell application "Safari"
    if (count of windows) > 0 then
        return URL of current tab of front window
    end if
    return ""
end tell
'''

CHROME_SCRIPT = '''
tell application "Google Chrome"
    if (count of windows) > 0 then
        return URL of active tab of front window
    end if
    return ""
end tell
'''

IDLE_SPLIT_SECS = 30 * 60


def _log(msg):
    os.makedirs(CLD_DIR, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")


def _run_applescript(script):
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_current_url():
    for script in [SAFARI_SCRIPT, CHROME_SCRIPT]:
        url = _run_applescript(script)
        if url:
            return url
    return ""


def _load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"active": False, "start_time": None, "session_id": None, "url": None}


def _save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def _save_web_session(state, end_time):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from db import insert_session
    start    = datetime.fromisoformat(state["start_time"])
    duration = max(1, int((end_time - start).total_seconds() / 60))
    s = {
        "id":           state["session_id"],
        "timestamp":    state["start_time"],
        "source":       "web",
        "model":        "claude.ai",
        "project":      "",
        "task":         "",
        "category":     "other",
        "tokens_in":    0,
        "tokens_out":   0,
        "cost_pct":     0.0,
        "duration_min": duration,
        "synced":       0,
    }
    insert_session(s)
    _log(f"Saved web session {state['session_id']} duration={duration}min")


def run_daemon():
    os.makedirs(CLD_DIR, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from db import init_db
    init_db()
    _log(f"Daemon started PID={os.getpid()}")

    state = _load_state()

    def _handle_signal(sig, frame):
        _log("Daemon stopping on signal")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    while True:
        try:
            url = _get_current_url()
            now = datetime.now()
            is_claude = "claude.ai" in url

            if is_claude:
                if not state["active"]:
                    state["active"]     = True
                    state["start_time"] = now.isoformat()
                    state["session_id"] = "web-" + str(uuid.uuid4())[:8]
                    state["url"]        = url
                    _log(f"Session started: {state['session_id']}")
                else:
                    start   = datetime.fromisoformat(state["start_time"])
                    elapsed = (now - start).total_seconds()
                    if elapsed > IDLE_SPLIT_SECS and state["url"] == url:
                        _save_web_session(state, now)
                        state["start_time"] = now.isoformat()
                        state["session_id"] = "web-" + str(uuid.uuid4())[:8]
                        _log(f"Session split → {state['session_id']}")
            else:
                if state["active"]:
                    _save_web_session(state, now)
                    state["active"]     = False
                    state["start_time"] = None
                    state["session_id"] = None
                    state["url"]        = None

            _save_state(state)
        except Exception as e:
            _log(f"Loop error: {e}")

        time.sleep(30)


def cmd_start():
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = f.read().strip()
        try:
            os.kill(int(pid), 0)
            print(f"Daemon already running (PID {pid})")
            return
        except ProcessLookupError:
            os.remove(PID_FILE)

    os.makedirs(CLD_DIR, exist_ok=True)
    script = os.path.abspath(__file__)
    with open(LOG_FILE, "a") as log:
        proc = subprocess.Popen(
            [sys.executable, script, "_run"],
            stdout=log, stderr=log,
            start_new_session=True,
        )
    print(f"Daemon started (PID {proc.pid})")


def cmd_stop():
    if not os.path.exists(PID_FILE):
        print("Daemon not running.")
        return
    with open(PID_FILE) as f:
        pid = int(f.read().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Daemon stopped (PID {pid})")
    except ProcessLookupError:
        print("Daemon was not running (stale PID removed)")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def cmd_status():
    if not os.path.exists(PID_FILE):
        print("Daemon: stopped")
        return
    with open(PID_FILE) as f:
        pid = f.read().strip()
    try:
        os.kill(int(pid), 0)
        print(f"Daemon: running (PID {pid})")
        state = _load_state()
        if state.get("active"):
            print(f"  Claude.ai active since {state['start_time']}")
        else:
            print("  Claude.ai: not active")
    except ProcessLookupError:
        print("Daemon: stopped (stale PID file)")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "start":
        cmd_start()
    elif cmd == "stop":
        cmd_stop()
    elif cmd == "status":
        cmd_status()
    elif cmd == "_run":
        run_daemon()
    else:
        print("Usage: daemon.py start|stop|status")
        sys.exit(1)


if __name__ == "__main__":
    main()
