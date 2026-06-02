import os
import requests
from db import get_unsynced, get_today, get_week, get_month, mark_synced


def _load_gas_url():
    url = os.environ.get("CLD_GAS_URL", "")
    if url:
        return url
    env_path = os.path.expanduser("~/yamane/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("CLD_GAS_URL="):
                    return line.split("=", 1)[1]
    return ""


def sync_sessions():
    url = _load_gas_url()
    if not url:
        print("CLD_GAS_URL not set. Run: echo 'CLD_GAS_URL=<url>' >> ~/yamane/.env")
        return

    rows = get_unsynced()
    if not rows:
        print("Nothing to sync.")
        return

    synced_ids = []
    for s in rows:
        payload = {"action": "saveClaudeLog", "data": s}
        try:
            resp = requests.post(url, json=payload, timeout=30)
            result = resp.json()
            if result.get("ok"):
                synced_ids.append(s["id"])
                print(f"  ok  {s['id'][:12]}  [{s['source']}]  {s.get('model','')[:30]}")
            else:
                print(f"  ERR {s['id'][:12]}  {result.get('error','?')}")
        except Exception as e:
            print(f"  ERR {s['id'][:12]}  {e}")

    if synced_ids:
        mark_synced(synced_ids)

    print(f"\nSynced {len(synced_ids)}/{len(rows)} sessions.")


def resync_sessions(scope="today"):
    url = _load_gas_url()
    if not url:
        print("CLD_GAS_URL not set. Run: echo 'CLD_GAS_URL=<url>' >> ~/yamane/.env")
        return

    if scope == "week":
        rows = get_week()
    elif scope == "month":
        rows = get_month()
    else:
        rows = get_today()

    if not rows:
        print(f"No sessions in scope: {scope}")
        return

    ok_count = 0
    for s in rows:
        payload = {"action": "saveClaudeLog", "data": s}
        try:
            resp = requests.post(url, json=payload, timeout=30)
            result = resp.json()
            if result.get("ok"):
                ok_count += 1
                task = s.get("task") or "(unlabeled)"
                print(f"  ok  {s['id'][:12]}  [{s.get('category','?')}]  {task[:30]}")
            else:
                print(f"  ERR {s['id'][:12]}  {result.get('error','?')}")
        except Exception as e:
            print(f"  ERR {s['id'][:12]}  {e}")

    print(f"\nResynced {ok_count}/{len(rows)} sessions ({scope}).")
