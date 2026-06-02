"""Read the live session JSONL for real-time /statusline equivalent."""
import os
import json
import glob
from datetime import datetime, timedelta, timezone
from config import CLAUDE_PROJECTS_DIR, PRICING, PRO_MONTHLY_USD

CONTEXT_MAX = 200_000


def _next_friday_reset():
    now = datetime.now()
    days = (4 - now.weekday()) % 7        # 4 = Friday
    if days == 0 and now.hour >= 6:
        days = 7
    reset = (now + timedelta(days=days)).replace(
        hour=6, minute=0, second=0, microsecond=0)
    if reset.date() == now.date():
        return "Today06:00"
    return f"{reset.strftime('%a')}06:00"


def _reset_countdown(reset_dt):
    """'Xh Ym' until reset_dt, or 'HH:MM' if < 6h away."""
    now  = datetime.now()
    diff = (reset_dt - now).total_seconds()
    if diff <= 0:
        return "now"
    h = int(diff // 3600)
    m = int((diff % 3600) // 60)
    if h < 6:
        return f"{h}h {m:02d}m"
    return reset_dt.strftime("%H:%M")


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
    first_ts_local = None

    try:
        with open(latest, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    e   = json.loads(line)
                    if not project and e.get("cwd"):
                        project = os.path.basename(e["cwd"])
                    # Capture first timestamp for reset calc
                    if not first_ts_local and e.get("timestamp"):
                        ts_utc = datetime.fromisoformat(
                            e["timestamp"].replace("Z", "+00:00"))
                        first_ts_local = ts_utc.astimezone().replace(tzinfo=None)
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

    # Session reset = first timestamp + 5 hours
    session_reset    = (first_ts_local + timedelta(hours=5)) if first_ts_local else None
    session_reset_str = _reset_countdown(session_reset) if session_reset else "—"
    weekly_reset_str  = _next_friday_reset()

    return {
        "model":             model,
        "project":           project or "—",
        "context_tokens":    context_tokens,
        "context_pct":       ctx_pct,
        "tokens_in":         total_in + total_cache,
        "tokens_out":        total_out,
        "cost_pct":          cost_pct,
        "session_reset":     session_reset_str,
        "weekly_reset":      weekly_reset_str,
    }
