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

CTX_BAR_W  = 20
COST_BAR_W = 10


def _ctx_bar(pct):
    filled = min(CTX_BAR_W, int(pct / 100 * CTX_BAR_W))
    color  = "green" if pct < 60 else ("yellow" if pct < 85 else "red")
    t = Text()
    t.append("█" * filled,               style=f"bold {color}")
    t.append("░" * (CTX_BAR_W - filled), style="dim")
    return t


def _cost_bar(pct, max_val, color="green"):
    if max_val <= 0:
        max_val = 0.001
    filled = min(COST_BAR_W, int(pct / max_val * COST_BAR_W))
    t = Text()
    t.append("█" * filled,                style=f"bold {color}")
    t.append("░" * (COST_BAR_W - filled), style="dim")
    return t


def _pct_color(pct):
    if pct < 1.0: return "green"
    if pct < 3.0: return "yellow"
    return "red"


def _two_col(label1, pct1, color1, label2, pct2, color2, max_val):
    t = Text()
    t.append(f"{label1:<8}", style="dim")
    t.append_text(_cost_bar(pct1, max_val, color1))
    t.append(f"  {pct1:.3f}%   ", style=color1)
    t.append(f"{label2:<7}", style="dim")
    t.append_text(_cost_bar(pct2, max_val, color2))
    t.append(f"  {pct2:.3f}%", style=color2)
    return t


def _main_panel(today, h5, week, month, live):
    now         = time.strftime("%H:%M:%S")
    session_pct = live["cost_pct"]   if live else (today[0].get("cost_pct", 0) if today else 0)
    h5_pct      = sum(s.get("cost_pct", 0) for s in h5)
    week_pct    = sum(s.get("cost_pct", 0) for s in week)
    month_pct   = sum(s.get("cost_pct", 0) for s in month)
    code_pct    = sum(s.get("cost_pct", 0) for s in month if s.get("source") == "code")
    web_pct     = sum(s.get("cost_pct", 0) for s in month if s.get("source") == "web")
    max_val     = max(session_pct, h5_pct, week_pct, month_pct, code_pct, 0.001)

    lines = []

    # Live session row
    if live:
        model   = live["model"] or "—"
        project = live["project"] or "—"
        ctx_pct = live["context_pct"]
        ctx_k   = live["context_tokens"] // 1000
        t = Text()
        t.append("LIVE  ", style="bold green")
        t.append(f"{model}  ", style="cyan")
        t.append(f"{project}", style="dim")
        lines.append(t)

        t2 = Text()
        t2.append("Context  ", style="dim")
        t2.append_text(_ctx_bar(ctx_pct))
        t2.append(f"  {ctx_pct:.1f}%  ", style="bold" + (" green" if ctx_pct < 60 else " yellow" if ctx_pct < 85 else " red"))
        t2.append(f"({ctx_k}K / 200K tokens)", style="dim")
        lines.append(t2)
        lines.append(Text("─" * 58, style="dim"))
    else:
        lines.append(Text("LIVE  —  (no active session)", style="dim"))
        lines.append(Text("─" * 58, style="dim"))

    lines.append(_two_col("Session", session_pct, "cyan",
                           "5hr    ", h5_pct,      "yellow",    max_val))
    lines.append(_two_col("Week   ", week_pct, _pct_color(week_pct),
                           "Month  ", month_pct, _pct_color(month_pct), max_val))
    lines.append(_two_col("Code   ", code_pct, "blue",
                           "Web    ", web_pct,  "magenta",  max_val))

    return Panel(Group(*lines), title=f"clduse  {now}",
                 title_align="left", style="cyan",
                 padding=(0, 1), expand=False)


def _log_panel(today):
    t = Table(show_header=False, box=None, padding=(0, 1), expand=False)
    t.add_column("Time",  style="dim",  width=5,  no_wrap=True)
    t.add_column("Src",               width=5,  no_wrap=True)
    t.add_column("Task",              width=32, no_wrap=True)
    t.add_column("Cost%", justify="right", width=8, style="dim")

    for s in today[:6]:
        ts   = s.get("timestamp", "")
        task = s.get("task") or ("(active)" if s.get("source") == "web" else "—")
        t.add_row(
            ts[11:16] if len(ts) >= 16 else "",
            s.get("source", ""),
            task[:32],
            f"{s.get('cost_pct', 0):.3f}%",
        )

    return Panel(t, title="TODAY LOG", title_align="left",
                 style="white", padding=(0, 0), expand=False)


def _footer():
    return Text(
        "  Ctrl+C exit  │  new terminal: "
        "clduse log/sync/resync/today/week/daemon",
        style="dim"
    )


def show_dashboard():
    init_db()
    try:
        with Live(refresh_per_second=0.2, screen=False) as live:
            while True:
                today   = get_today()
                week    = get_week()
                month   = get_month()
                h5      = get_recent_hours(5)
                session = read_live()

                live.update(Group(
                    _main_panel(today, h5, week, month, session),
                    _log_panel(today),
                    _footer(),
                ))
                time.sleep(5)
    except KeyboardInterrupt:
        pass


def show_today():
    """Detailed today table — debugging."""
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
    """Render heatmap — called from analysis.show_week()."""
    from rich.console import Console
    from rich.text import Text

    console = Console()
    today   = date.today()
    weekday = today.weekday()
    days    = [today - timedelta(days=weekday - i) for i in range(7)]

    TIME_BANDS = [
        ("AM",  6, 12),
        ("PM", 12, 18),
        ("Eve",18, 24),
        ("Ngt", 0,  6),
    ]

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
