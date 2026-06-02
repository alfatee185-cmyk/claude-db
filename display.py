import time
from datetime import date, datetime, timedelta
from collections import defaultdict
from rich.console import Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from db import get_today, get_week, get_month, get_recent_hours, init_db
from config import PRO_MONTHLY_USD

TIME_BANDS = [
    ("AM",  6, 12),
    ("PM", 12, 18),
    ("Eve",18, 24),
    ("Ngt", 0,  6),
]

BAR_W  = 14   # chars for progress bars
BAR_MAX = 5.0  # 5% = full bar (scales well for daily usage)


def _bar(pct, color="green"):
    filled = min(BAR_W, int(pct / BAR_MAX * BAR_W))
    empty  = BAR_W - filled
    t = Text()
    t.append("█" * filled, style=f"bold {color}")
    t.append("░" * empty,  style="dim")
    return t


def _pct_color(pct):
    if pct < 1.0:
        return "green"
    elif pct < 3.0:
        return "yellow"
    return "red"


def _stats_panel(today, h5, month):
    now         = time.strftime("%H:%M:%S")
    session_pct = today[0].get("cost_pct", 0) if today else 0
    h5_pct      = sum(s.get("cost_pct", 0) for s in h5)
    month_pct   = sum(s.get("cost_pct", 0) for s in month)
    code_pct    = sum(s.get("cost_pct", 0) for s in month if s.get("source") == "code")
    web_pct     = sum(s.get("cost_pct", 0) for s in month if s.get("source") == "web")
    latest_proj = today[0].get("project", "") if today else ""

    rows = [
        Text(f"clduse  {now}", style="bold cyan"),
        Text(""),
        _stat_row("Session", session_pct, "cyan"),
        _stat_row("5hr    ", h5_pct,      "yellow"),
        _stat_row("Month  ", month_pct,   _pct_color(month_pct)),
        Text(""),
        _stat_row("Code   ", code_pct,    "blue"),
        _stat_row("Web    ", web_pct,     "magenta"),
    ]
    if latest_proj:
        rows += [Text(""), Text(f" [{latest_proj}]", style="dim")]

    content = Group(*rows)
    return Panel(content, style="cyan", padding=(1, 2))


def _stat_row(label, pct, color):
    t = Text()
    t.append(f" {label}  ", style="dim")
    t.append_text(_bar(pct, color))
    t.append(f"  {pct:.3f}%", style=color)
    return t


def _heatmap_cell(val, max_val):
    if val <= 0:
        return Text(" · ", style="dim")
    ratio = val / max_val if max_val > 0 else 0
    if ratio < 0.25:
        return Text(" ■ ", style="bold dark_green")
    elif ratio < 0.6:
        return Text(" ■ ", style="bold yellow")
    else:
        return Text(" ■ ", style="bold red")


def _heatmap_panel(sessions_week):
    today   = date.today()
    weekday = today.weekday()
    days    = [today - timedelta(days=weekday - i) for i in range(7)]

    grid = defaultdict(float)
    for s in sessions_week:
        try:
            ts = datetime.fromisoformat(s["timestamp"])
            d  = ts.date()
            h  = ts.hour
            for band, h0, h1 in TIME_BANDS:
                if h0 <= h < h1:
                    grid[(d, band)] += s.get("cost_pct", 0)
                    break
        except Exception:
            pass

    max_val = max(grid.values(), default=0.001)

    t = Table(show_header=True, header_style="dim", box=None, padding=(0, 0))
    t.add_column("   ", style="dim", width=4, no_wrap=True)
    for d in days:
        t.add_column(d.strftime("%a"), justify="center", width=4, no_wrap=True)

    for band, h0, h1 in TIME_BANDS:
        row = [Text(band, style="dim")]
        for d in days:
            row.append(_heatmap_cell(grid.get((d, band), 0), max_val))
        t.add_row(*row)

    return Panel(Align.center(t, vertical="middle"), title="HEATMAP",
                 style="blue", padding=(1, 1))


def _footer():
    return Text("  [q]quit  [l]log  [w]week  [s]sync  [r]resync  [t]today  [d]daemon",
                style="dim")


def show_dashboard():
    init_db()
    try:
        with Live(refresh_per_second=0.2, screen=True) as live:
            while True:
                today = get_today()
                week  = get_week()
                month = get_month()
                h5    = get_recent_hours(5)

                layout = Layout()
                layout.split_column(
                    Layout(name="top",    ratio=1),
                    Layout(name="footer", size=1),
                )
                layout["top"].split_row(
                    Layout(name="stats",   ratio=5),
                    Layout(name="heatmap", ratio=6),
                )
                layout["stats"].update(_stats_panel(today, h5, month))
                layout["heatmap"].update(_heatmap_panel(week))
                layout["footer"].update(_footer())

                live.update(layout)
                time.sleep(5)
    except KeyboardInterrupt:
        pass


def show_today():
    """Separate today view for debugging — called via clduse today."""
    from rich.console import Console
    from db import get_today
    init_db()
    console = Console()
    today = get_today()
    if not today:
        console.print("[dim]No sessions today.[/]")
        return

    t = Table(show_header=True, header_style="bold magenta", expand=True)
    t.add_column("Time",   style="dim", width=6,  no_wrap=True)
    t.add_column("Src",               width=5,  no_wrap=True)
    t.add_column("Model",             width=22, no_wrap=True)
    t.add_column("Project",           width=16, no_wrap=True)
    t.add_column("Task",              width=30, no_wrap=True)
    t.add_column("Tokens↑",  justify="right", width=8)
    t.add_column("Tokens↓",  justify="right", width=8)
    t.add_column("Cost%",    justify="right", width=8)

    total = 0.0
    for s in today:
        ts    = s.get("timestamp", "")
        total += s.get("cost_pct", 0)
        t.add_row(
            ts[11:16] if len(ts) >= 16 else "",
            s.get("source", ""),
            s.get("model", "")[:22],
            s.get("project", "")[:16],
            (s.get("task") or "—")[:30],
            f"{s.get('tokens_in',0):,}",
            f"{s.get('tokens_out',0):,}",
            f"{s.get('cost_pct', 0):.3f}%",
        )

    console.print(Panel(t, title=f"TODAY  ({len(today)} sessions  {total:.3f}% total)"))
