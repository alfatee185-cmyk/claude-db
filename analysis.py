from collections import defaultdict
from db import get_week, init_db


def show_week():
    init_db()
    sessions = get_week()
    if not sessions:
        print("No sessions this week.")
        return

    total_pct = sum(s.get("cost_pct", 0) for s in sessions)
    code_pct  = sum(s.get("cost_pct", 0) for s in sessions if s.get("source") == "code")
    web_pct   = sum(s.get("cost_pct", 0) for s in sessions if s.get("source") == "web")
    unlabeled = sum(1 for s in sessions if not s.get("task"))

    by_cat = defaultdict(float)
    for s in sessions:
        by_cat[s.get("category", "other")] += s.get("cost_pct", 0)

    print(f"\n{'='*40}")
    print(f"  WEEK ANALYSIS")
    print(f"{'='*40}")
    print(f"  Total : {total_pct:.2f}%")
    print(f"  Code  : {code_pct:.2f}%   Web: {web_pct:.2f}%")
    print(f"  Sessions: {len(sessions)}  (unlabeled: {unlabeled})")
    print()
    print("  By category:")
    for cat, pct in sorted(by_cat.items(), key=lambda x: -x[1]):
        bar_len = min(20, int(pct * 2))
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"    {cat:<10} {bar} {pct:.2f}%")

    print()
    top3 = sorted(sessions, key=lambda s: -s.get("cost_pct", 0))[:3]
    print("  Top 3 sessions:")
    for s in top3:
        ts   = s.get("timestamp", "")[:16]
        task = (s.get("task") or "(unlabeled)")[:30]
        pct  = s.get("cost_pct", 0)
        print(f"    {ts}  {task}  {pct:.3f}%")

    debug_pct = by_cat.get("debug", 0)
    plan_pct  = by_cat.get("plan", 0)
    if plan_pct > 0 and debug_pct > plan_pct * 2:
        print("\n  [insight] High debug:plan ratio — consider more upfront planning.")
    if unlabeled > len(sessions) * 0.5:
        print(f"\n  [insight] {unlabeled} unlabeled sessions — run: clduse log \"task\" to categorize.")
    print()

    from display import show_heatmap
    show_heatmap(sessions)
