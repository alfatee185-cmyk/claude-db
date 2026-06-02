import os
import json
import glob
from datetime import datetime
from config import CLAUDE_PROJECTS_DIR, PRICING, PRO_MONTHLY_USD


def _cost_pct(model, tokens_in, tokens_out):
    prices = PRICING.get(model, {"input": 3.00, "output": 15.00})
    cost = (tokens_in * prices["input"] + tokens_out * prices["output"]) / 1_000_000
    return round(cost / PRO_MONTHLY_USD * 100, 4)


def scan_sessions():
    pattern = os.path.join(CLAUDE_PROJECTS_DIR, "**", "*.jsonl")
    files = glob.glob(pattern, recursive=True)

    seen = set()
    sessions = []

    for fpath in files:
        project = os.path.basename(os.path.dirname(fpath))
        try:
            with open(fpath, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    sid = entry.get("sessionId") or entry.get("session_id") or ""
                    if not sid or sid in seen:
                        continue
                    seen.add(sid)

                    model = entry.get("model", "")
                    usage = entry.get("usage", {}) or {}
                    tokens_in  = int(usage.get("input_tokens", 0) or 0)
                    tokens_out = int(usage.get("output_tokens", 0) or 0)
                    ts = entry.get("timestamp", datetime.now().isoformat())

                    sessions.append({
                        "id": sid,
                        "timestamp": ts,
                        "source": "code",
                        "model": model,
                        "project": project,
                        "task": "",
                        "category": "other",
                        "tokens_in": tokens_in,
                        "tokens_out": tokens_out,
                        "cost_pct": _cost_pct(model, tokens_in, tokens_out),
                        "duration_min": 0,
                        "synced": 0,
                    })
        except Exception:
            continue

    return sessions
