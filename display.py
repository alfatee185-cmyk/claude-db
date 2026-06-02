import time
from datetime import date, datetime, timedelta
from collections import defaultdict
from rich.console import Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from db import get_today, get_week, get_month, get_recent_hours, init_db
from config import PRO_MONTHLY_USD

TIME_BANDS = [
    ("AM",  6, 12),
    ("PM", 12, 18),
    ("Eve",18, 24),
    ("Ngt", 0,  6),
]


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
    t.add_column("    ", style="dim", width=4, no_wrap=True)
    for d in days:
        t.add_column(d.strftime("%a"), justify="center", width=4, no_wrap=True)

    for band, h0, h1 in TIME_BANDS:
        row = [Text(band, style="dim")]
        for d in days:
            row.append(_heatmap_cell(grid.get((d, band), 0), max_val))
        t.add_row(*row)

    return Panel(t, title="HEATMAP", style="blue", padding=(0, 1))


def _header_panel(today, h5, month):
    now         = time.strftime("%H:%M:%S")
    session_pct = today[0].get("cost_pct", 0) if today else 0
    h5_pct      = sum(s.get("cost_pct", 0) for s in h5)
    month_pct   = sum(s.get("cost_pct", 0) for s in month)
    code_pct    = sum(s.get("cost_pct", 0) for s in month if s.get("source") == "code")
    web_pct     = sum(s.get("cost_pct", 0) for s in month if s.get("source") == "web")

    t = Text()
    t.append("clduse", style="bold cyan")
    t.append(f"  {now}  ", style="dim")
    t.append("│  Session ", style="dim")
    t.append(f"{session_pct:.3f}%", style="cyan")
    t.append("  │  5hr ", style="dim")
    t.append(f"{h5_pct:.3f}%", style="yellow")
    t.append("  │  Month ", style="dim")
    t.append(f"{month_pct:.2f}%", style="green")
    t.append(f"  (Code {code_pct:.2f}% / Web {web_pct:.2f}%)", style="dim")
    return Panel(t, style="cyan", padding=(0, 1))


def _today_table(today):
    t = Table(show_header=True, header_style="bold magenta", expand=True,
              padding=(0, 1), show_edge=True)
    t.add_column("Time",  style="dim", width=6,  no_wrap=True)
    t.add_column("Src",              width=5,  no_wrap=True)
    t.add_column("Model",            width=20, no_wrap=True)
    t.add_column("Task",             width=28, no_wrap=True)
    t.add_column("Tokens",           width=14, no_wrap=True)
    t.add_column("Cost%",            width=8,  no_wrap=True, justify="right")

    for s in today[:8]:
        ts  = s.get("timestamp", "")
        tok = f"{s.get('tokens_in',0):,}↑ {s.get('tokens_out',0):,}↓"
        t.add_row(
            ts[11:16] if len(ts) >= 16 else "",
            s.get("source", ""),
            s.get("model", "")[:20],
            (s.get("task") or "—")[:28],
            tok,
            f"{s.get('cost_pct', 0):.3f}%",
        )
    return Panel(t, title="TODAY", padding=(0, 0))


def _footer():
    return Text("  [q]quit  [l]log  [w]week  [s]sync  [r]resync  [d]daemon", style="dim")


def show_dashboard():
    init_db()
    try:
        with Live(refresh_per_second=0.2, screen=True) as live:
            while True:
                today = get_today()
                week  = get_week()
                month = get_month()
                h5    = get_recent_hours(5)
                live.update(Group(
                    _header_panel(today, h5, month),
                    _heatmap_panel(week),
                    _today_table(today),
                    _footer(),
                ))
                time.sleep(5)
    except KeyboardInterrupt:
        pass
