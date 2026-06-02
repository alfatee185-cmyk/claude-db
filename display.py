import time
from datetime import date, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.console import Group
from db import get_today, get_week, get_month, init_db
from config import PRO_MONTHLY_USD

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _week_bars(sessions):
    today   = date.today()
    weekday = today.weekday()
    day_map = {}
    for s in sessions:
        try:
            d = date.fromisoformat(s["timestamp"][:10])
            day_map[d] = day_map.get(d, 0) + s.get("cost_pct", 0)
        except Exception:
            pass

    lines = []
    for i in range(7):
        if i <= weekday:
            d   = today - timedelta(days=weekday - i)
            pct = day_map.get(d, 0)
            bar_len = min(20, int(pct * 2))
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {DAYS[i]}  {bar}  {pct:.1f}%")
        else:
            lines.append(f"  {DAYS[i]}  {'░' * 20}  -")
    return "\n".join(lines)


def _status_panel():
    now = time.strftime("%H:%M:%S")
    return Panel(f"[bold cyan]clduse[/] — Claude Usage Monitor    [dim]{now}[/]", style="cyan")


def _monthly_panel(month):
    total = sum(s.get("cost_pct", 0) for s in month)
    code  = sum(s.get("cost_pct", 0) for s in month if s.get("source") == "code")
    web   = sum(s.get("cost_pct", 0) for s in month if s.get("source") == "web")
    bar_len = min(40, int(total * 0.4))
    bar = "█" * bar_len + "░" * (40 - bar_len)
    body = (
        f"  {total:.2f}% of ${PRO_MONTHLY_USD:.0f}/mo\n"
        f"  [{bar}]\n"
        f"  Code: {code:.2f}%   Web: {web:.2f}%"
    )
    return Panel(body, title="MONTHLY", style="green")


def _weekly_panel(week):
    return Panel(_week_bars(week), title="WEEKLY BARS", style="yellow")


def _today_table(today):
    table = Table(title="TODAY", header_style="bold magenta", expand=True)
    table.add_column("Time",   style="dim",    width=6)
    table.add_column("Src",                    width=5)
    table.add_column("Model",                  width=22)
    table.add_column("Task",                   width=28)
    table.add_column("Tokens",                 width=14)
    table.add_column("Cost%",                  width=8)

    for s in today[:10]:
        ts  = s.get("timestamp", "")
        t   = ts[11:16] if len(ts) >= 16 else ""
        tok = f"{s.get('tokens_in',0):,}↑ {s.get('tokens_out',0):,}↓"
        table.add_row(
            t,
            s.get("source", ""),
            s.get("model", "")[:22],
            (s.get("task") or "—")[:28],
            tok,
            f"{s.get('cost_pct', 0):.3f}%",
        )
    return table


def _footer():
    return Text("  [q]quit  [l]log  [w]week  [s]sync  [d]daemon", style="dim")


def show_dashboard():
    init_db()
    try:
        with Live(refresh_per_second=0.2, screen=True) as live:
            while True:
                today = get_today()
                week  = get_week()
                month = get_month()
                live.update(Group(
                    _status_panel(),
                    _monthly_panel(month),
                    _weekly_panel(week),
                    _today_table(today),
                    _footer(),
                ))
                time.sleep(5)
    except KeyboardInterrupt:
        pass
