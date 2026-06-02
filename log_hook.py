#!/usr/bin/env python3
"""Claude Code Stop hook — must be completely silent on stdout."""
import sys
import os
import json
import traceback
from datetime import datetime

_DIR = os.path.expanduser("~/.cld")
_HOOK_LOG = os.path.join(_DIR, "hook.log")


def _err(msg):
    os.makedirs(_DIR, exist_ok=True)
    with open(_HOOK_LOG, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)

        data = json.loads(raw)

        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from db import init_db, insert_session
        from config import PRICING, PRO_MONTHLY_USD

        init_db()

        model      = data.get("model", "")
        usage      = data.get("usage") or {}
        tokens_in  = int(usage.get("input_tokens", 0) or 0)
        tokens_out = int(usage.get("output_tokens", 0) or 0)

        prices   = PRICING.get(model, {"input": 3.00, "output": 15.00})
        cost_usd = (tokens_in * prices["input"] + tokens_out * prices["output"]) / 1_000_000
        cost_pct = round(cost_usd / PRO_MONTHLY_USD * 100, 4)

        cwd     = data.get("cwd", "") or ""
        project = os.path.basename(cwd) if cwd else ""

        sid = data.get("session_id") or data.get("sessionId") or ""
        if not sid:
            import uuid
            sid = str(uuid.uuid4())

        insert_session({
            "id":           sid,
            "timestamp":    datetime.now().isoformat(),
            "source":       "code",
            "model":        model,
            "project":      project,
            "task":         "",
            "category":     "other",
            "tokens_in":    tokens_in,
            "tokens_out":   tokens_out,
            "cost_pct":     cost_pct,
            "duration_min": 0,
            "synced":       0,
        })
    except Exception:
        _err(traceback.format_exc())

    sys.exit(0)


if __name__ == "__main__":
    main()
