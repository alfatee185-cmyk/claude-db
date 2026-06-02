"""Read live session data from ~/.cld/status.json (written by statusLine hook)."""
import os
import json
import glob
from datetime import datetime, timedelta
from config import CLAUDE_PROJECTS_DIR, PRICING, PRO_MONTHLY_USD

CONTEXT_MAX = 200_000
STATUS_JSON = os.path.expanduser("~/.cld/status.json")


def _ts_to_countdown(ts):
    if not ts:
        return "—"
    try:
        dt   = datetime.fromtimestamp(float(ts))
        diff = (dt - datetime.now()).total_seconds()
        if diff <= 0:
            return "now"
        h = int(diff // 3600)
        m = int((diff % 3600) // 60)
        return f"{h}h{m:02d}m" if h < 6 else dt.strftime("%H:%M")
    except Exception:
        return "—"


def _ts_to_day(ts):
    if not ts:
        return "—"
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%a%H:%M")
    except Exception:
        return "—"


def _next_friday_reset():
    now  = datetime.now()
    days = (4 - now.weekday()) % 7
    if days == 0 and now.hour >= 6:
        days = 7
    reset = (now + timedelta(days=days)).replace(
        hour=6, minute=0, second=0, microsecond=0)
    return reset.strftime("%a%H:%M") if reset.date() != now.date() else "Today06:00"


def read_live():
    """Return live session data. Primary: status.json. Fallback: JSONL."""

    # ── Primary: status.json (written every statusLine tick) ──────────────
    if os.path.exists(STATUS_JSON):
        try:
            with open(STATUS_JSON) as f:
                d = json.load(f)

            ctx   = d.get("context_window", {})
            cost  = d.get("cost", {})
            fh    = d.get("rate_limits", {}).get("five_hour", {})
            wk    = d.get("rate_limits", {}).get("seven_day", {})
            model = d.get("model", {}).get("id", "")
            cwd   = (d.get("workspace", {}).get("current_dir", "")
                     or d.get("cwd", ""))
            project = os.path.basename(cwd) if cwd else "—"

            ctx_used = float(ctx.get("used_percentage", 0))
            ctx_tok  = ctx.get("current_usage", {}).get("cache_read_input_tokens", 0)

            cost_usd = float(cost.get("total_cost_usd", 0))
            cost_pct = round(cost_usd / PRO_MONTHLY_USD * 100, 2)

            fh_pct      = fh.get("used_percentage")
            fh_reset_ts = fh.get("resets_at")
            wk_pct      = wk.get("used_percentage")
            wk_reset_ts = wk.get("resets_at")

            return {
                "model":          model,
                "project":        project,
                "context_tokens": ctx_tok,
                "context_pct":    ctx_used,
                "cost_usd":       cost_usd,
                "cost_pct":       cost_pct,
                "fh_pct":         float(fh_pct) if fh_pct is not None else None,
                "fh_reset":       _ts_to_countdown(fh_reset_ts),
                "wk_pct":         float(wk_pct) if wk_pct is not None else None,
                "wk_reset":       _ts_to_day(wk_reset_ts) or _next_friday_reset(),
                "source":         "status",
            }
        except Exception:
            pass

    # ── Fallback: JSONL parsing ────────────────────────────────────────────
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
    cost_pct = round(cost_usd / PRO_MONTHLY_USD * 100, 2)
    ctx_pct  = round(context_tokens / CONTEXT_MAX * 100, 1)
    session_reset = (first_ts_local + timedelta(hours=5)) if first_ts_local else None

    return {
        "model":          model,
        "project":        project or "—",
        "context_tokens": context_tokens,
        "context_pct":    ctx_pct,
        "cost_usd":       cost_usd,
        "cost_pct":       cost_pct,
        "fh_pct":         None,
        "fh_reset":       _ts_to_countdown(session_reset.timestamp() if session_reset else None),
        "wk_pct":         None,
        "wk_reset":       _next_friday_reset(),
        "source":         "jsonl",
    }
