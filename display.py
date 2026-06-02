import os
import sys
import time
from datetime import date, datetime, timedelta
from collections import defaultdict
from rich.console import Group, Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from db import get_today, get_week, get_month, get_recent_hours, init_db
from live_session import read_live, CONTEXT_MAX
from config import PRO_MONTHLY_USD


def _term_width():
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 90


def _bar100(pct, width):
    """Bar on 0-100% scale with gradient: green→yellow→red by actual value."""
    pct    = max(0, min(100, pct))
    filled = min(width, max(0, int(pct / 100 * width)))
    t = Text()
    for i in range(filled):
        pos = (i / width) * 100   # 0-100 position in bar
        if pos < 50:
            t.append("█", style="bold green")
        elif pos < 75:
            t.append("█", style="bold yellow")
        else:
            t.append("█", style="bold red")
    t.append("░" * (width - filled), style="dim red" if pct > 85 else "dim")
    return t


def _pct_color100(pct):
    if pct < 50:  return "green"
    if pct < 75:  return "yellow"
    return "bold red"


def _main_panel(today, h5, week, month, live_data):
    now = time.strftime("%H:%M:%S")
    tw  = _term_width()
    bar_ctx = max(10, min(22, tw - 58))
    bar_w   = max(5,  min(8,  (tw - 84) // 3))

    # --- Real rate-limit values from statusLine JSON (via ~/.cld/status.json) ---
    ctx_pct  = live_data["context_pct"]           if live_data else 0
    fh_pct   = live_data.get("fh_pct")            if live_data else None   # 5hr rate limit %
    fh_reset = live_data.get("fh_reset", "—")     if live_data else "—"
    wk_pct   = live_data.get("wk_pct")            if live_data else None   # weekly rate limit %
    wk_reset = live_data.get("wk_reset", "—")     if live_data else "—"

    # Cost tracking from SQLite (separate metric, shown as Mo)
    month_pct = sum(s.get("cost_pct", 0) for s in month)
    code_pct  = sum(s.get("cost_pct", 0) for s in month if s.get("source") == "code")
    web_pct   = sum(s.get("cost_pct", 0) for s in month if s.get("source") == "web")

    # --- Line 1: LIVE + context (0-100%) ---
    line1 = Text()
    if live_data:
        model   = (live_data["model"] or "—")[:22]
        project = (live_data["project"] or "—")[:14]
        line1.append("LIVE ", style="bold green")
        line1.append(f"{model}  ", style="cyan")
        line1.append(f"{project}  ", style="dim")
        line1.append("│  Ctx ", style="dim")
        line1.append_text(_bar100(ctx_pct, bar_ctx))
        line1.append(f"  {ctx_pct:.1f}%", style=_pct_color100(ctx_pct))
        line1.append(f"  ↻{fh_reset}", style="dim")
    else:
        line1.append("No active session", style="dim")

    # --- Line 2: 5hr | Week | Mo (cost) ---
    def _seg100(label, pct, reset_hint=None, fmt=".0f"):
        t = Text()
        t.append(f"{label} ", style="dim")
        if pct is not None:
            t.append_text(_bar100(pct, bar_w))
            t.append(f" {pct:{fmt}}%", style=_pct_color100(pct))
        else:
            t.append("░" * bar_w, style="dim")
            t.append(" —%", style="dim")
        if reset_hint:
            t.append(f" ↻{reset_hint}", style="dim")
        return t

    line2 = Text()
    line2.append_text(_seg100("5hr", fh_pct, fh_reset))
    line2.append("  │  ", style="dim")
    line2.append_text(_seg100("Wk", wk_pct, wk_reset))
    line2.append("  │  ", style="dim")
    line2.append_text(_seg100("Mo", month_pct if month_pct else None, fmt=".2f"))
    if tw >= 90:
        line2.append(f"  Co {code_pct:.2f}%", style="blue")
        line2.append(f"  Wb {web_pct:.2f}%", style="magenta")

    return Panel(
        Group(line1, line2),
        title=f"clduse  {now}",
        title_align="left",
        style="cyan",
        padding=(0, 1),
        expand=False,
    )


def _footer():
    return Text(
        "  Ctrl+C exit  │  new terminal: "
        "clduse log/sync/resync/today/week/daemon",
        style="dim"
    )


def show_dashboard():
    # Snap terminal to exact fit: 85 cols × 5 rows
    if sys.stdout.isatty():
        sys.stdout.write("\033[8;5;85t")
        sys.stdout.flush()
        time.sleep(0.05)   # let the resize settle before first render

    init_db()
    try:
        with Live(refresh_per_second=0.2, screen=False) as live:
            while True:
                today = get_today()
                week  = get_week()
                month = get_month()
                h5    = get_recent_hours(5)
                sess  = read_live()

                live.update(Group(
                    _main_panel(today, h5, week, month, sess),
                    _footer(),
                ))
                time.sleep(5)
    except KeyboardInterrupt:
        pass


def show_today():
    console = Console()
    init_db()
    today = get_today()
    if not today:
        console.print("[dim]No sessions today.[/]")
        return
    t = Table(show_header=True, header_style="bold magenta", expand=False)
    t.add_column("Time",    style="dim", width=6,  no_wrap=True)
    t.add_column("Src",               width=5,  no_wrap=True)
    t.add_column("Model",             width=22, no_wrap=True)
    t.add_column("Project",           width=16, no_wrap=True)
    t.add_column("Task",              width=28, no_wrap=True)
    t.add_column("In",    justify="right", width=7)
    t.add_column("Out",   justify="right", width=7)
    t.add_column("Cost%", justify="right", width=8)
    total = 0.0
    for s in today:
        ts     = s.get("timestamp", "")
        total += s.get("cost_pct", 0)
        t.add_row(
            ts[11:16] if len(ts) >= 16 else "",
            s.get("source", ""),
            s.get("model", "")[:22],
            s.get("project", "")[:16],
            (s.get("task") or "—")[:28],
            f"{s.get('tokens_in',0):,}",
            f"{s.get('tokens_out',0):,}",
            f"{s.get('cost_pct', 0):.3f}%",
        )
    console.print(Panel(t,
        title=f"TODAY  {len(today)} sessions  {total:.3f}% total",
        title_align="left", expand=False))


def show_heatmap(sessions_week):
    console = Console()
    today   = date.today()
    weekday = today.weekday()
    days    = [today - timedelta(days=weekday - i) for i in range(7)]
    TIME_BANDS = [("AM", 6, 12), ("PM", 12, 18), ("Eve", 18, 24), ("Ngt", 0, 6)]
    grid = defaultdict(float)
    for s in sessions_week:
        try:
            ts = datetime.fromisoformat(s["timestamp"])
            d, h = ts.date(), ts.hour
            for band, h0, h1 in TIME_BANDS:
                if h0 <= h < h1:
                    grid[(d, band)] += s.get("cost_pct", 0)
                    break
        except Exception:
            pass
    max_val = max(grid.values(), default=0.001)
    t = Table(show_header=True, header_style="dim", box=None,
              padding=(0, 0), expand=False)
    t.add_column("   ", style="dim", width=4, no_wrap=True)
    for d in days:
        t.add_column(d.strftime("%a"), justify="center", width=4, no_wrap=True)
    for band, h0, h1 in TIME_BANDS:
        row = [Text(band, style="dim")]
        for d in days:
            val = grid.get((d, band), 0)
            if val <= 0:
                row.append(Text(" · ", style="dim"))
            else:
                ratio = val / max_val
                color = "dark_green" if ratio < 0.25 else ("yellow" if ratio < 0.6 else "red")
                row.append(Text(" ■ ", style=f"bold {color}"))
        t.add_row(*row)
    console.print(Panel(t, title="HEATMAP  (last 7 days)", title_align="left",
                        style="blue", padding=(0, 1), expand=False))
