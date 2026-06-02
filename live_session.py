"""Read the live session JSONL for real-time /statusline equivalent."""
import os
import json
import glob
from config import CLAUDE_PROJECTS_DIR, PRICING, PRO_MONTHLY_USD

CONTEXT_MAX = 200_000


def read_live():
    """Return live session stats from the most recently modified JSONL."""
    pattern = os.path.join(CLAUDE_PROJECTS_DIR, "**", "*.jsonl")
    files   = glob.glob(pattern, recursive=True)
    if not files:
        return None

    latest = max(files, key=os.path.getmtime)

    model = ""
    project = ""
    total_in = total_cache = total_out = 0
    context_tokens = 0

    try:
        with open(latest, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    e   = json.loads(line)
                    if not project and e.get("cwd"):
                        project = os.path.basename(e["cwd"])
                    msg = e.get("message", {}) or {}
                    u   = msg.get("usage") or e.get("usage") or {}
                    if u:
                        total_in    += u.get("input_tokens", 0)
                        total_cache += u.get("cache_creation_input_tokens", 0)
                        total_out   += u.get("output_tokens", 0)
                        context_tokens = u.get("cache_read_input_tokens", 0)
                    if msg.get("model"):
                        model = msg["model"]
                except Exception:
                    pass
    except Exception:
        return None

    prices   = PRICING.get(model, {"input": 3.00, "output": 15.00})
    cost_usd = ((total_in + total_cache) * prices["input"]
                + total_out * prices["output"]) / 1_000_000
    cost_pct = round(cost_usd / PRO_MONTHLY_USD * 100, 4)
    ctx_pct  = round(context_tokens / CONTEXT_MAX * 100, 1)

    return {
        "model":          model,
        "project":        project,
        "context_tokens": context_tokens,
        "context_pct":    ctx_pct,
        "tokens_in":      total_in + total_cache,
        "tokens_out":     total_out,
        "cost_pct":       cost_pct,
    }
