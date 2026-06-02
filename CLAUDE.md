# Claude Dashboard (clduse) — Session Context
Date: 2026-06-02
Load: every Claude Code session for claude-db project

---

## Project

```
Name     : claude-db (clduse)
Path     : ~/claude-db/
Command  : clduse
Python   : conda yamane (Python 3.11)
Git      : main branch
GitHub   : alfatee185-cmyk/claude-db
```

---

## Current Status (2026-06-02)

All components live on both Air and Mini:

| Component | Air | Mini |
|-----------|-----|------|
| Stop hook (log_hook.py) | ✅ | ✅ |
| Browser daemon (LaunchAgent) | ✅ | ✅ |
| clduse TUI (alias in .zshrc) | ✅ | ✅ |
| GAS + Google Sheet | ✅ deployed | reads same sheet |
| CLD_GAS_URL in .env | ✅ | ✅ |
| statusLine saves status.json | ✅ settings.json | ✅ statusline-command.sh |

### TUI — 85×5 auto-resize
```
╭─ clduse  HH:MM:SS ──────────────────────────────────────────────────────╮
│ LIVE model  project  │  Ctx [bar] ctx%  ↻Xh Ym                         │
│ 5hr [bar] X% ↻HH:MM  │  Wk [bar] X% ↻FriHH:MM  │  Mo [bar] X%        │
╰─────────────────────────────────────────────────────────────────────────╯
  Ctrl+C exit  │  new terminal: clduse log/sync/resync/today/week/daemon
```
Live data from `~/.cld/status.json` (written by statusLine every tick).
Bars: 0-100% scale, gradient green→yellow→red.

### Pending
- [ ] Auto-sync on Stop hook (currently manual: `clduse sync`)

---

## Git Workflow

```
Air = primary (develop + commit + push)
Mini = secondary (git pull to sync)

Flow: edit → git add -A → git commit → git push (Air)
      ssh Mini → cd ~/claude-db && git pull
```

---

## Key Data

```
GAS Project  : "Claude Dashboard" (script.google.com)
CLD_GAS_URL  : ~/yamane/.env
CLD_SHEET_ID : ~/yamane/.env  (1I5OqL7UOeedIUYbHFbEFlM_p-eQo19Pe87zS4BNB5Y8)
Google Sheet : LOG tab, 12 columns
```

---

## GAS — Claude Dashboard Project

```
GAS Project : "Claude Dashboard" (separate from Yamane)
env key     : CLD_GAS_URL (in ~/yamane/.env)
Sheet key   : CLD_SHEET_ID (in ~/yamane/.env)
Actions     : saveClaudeLog, getClaudeLogs, ping
```

### Deploy pattern
```
Execute as    : Me (her.alfa185@gmail.com)
Who has access: Anyone
URL format    : https://script.google.com/macros/s/[ID]/exec
Always use /exec — never /dev
Redeploy = New version every time code changes
```

---

## GAS Standard Rules (critical)

```
ES5 only — no const/let, no =>, no fetch(), no template literals
appendRow() for single rows
Max execution: 30s / Python timeout >= 30s
```

---

## Key Paths

```
~/claude-db/              project root (Air + Mini)
~/.cld/sessions.db        SQLite runtime data
~/.cld/status.json        statusLine JSON cache (rate limits, ctx%, cost)
~/.cld/daemon.pid         daemon PID
~/.cld/daemon.log         daemon log
~/.cld/hook.log           Stop hook errors only
~/.claude/settings.json   Air: Stop hook + statusLine save
~/.claude/statusline-command.sh  Mini: patched to save status.json
~/yamane/.env             CLD_GAS_URL + CLD_SHEET_ID
```

---

## Storage

```
Local  : ~/.cld/sessions.db (SQLite)
Remote : GAS → Google Sheets LOG tab
Sync   : clduse sync (manual)
```

---

## Services

```
clduse TUI  : terminal only, auto-resizes to 85×5
daemon      : background, PID in ~/.cld/daemon.pid, LaunchAgent on both machines
Stop hook   : ~/.claude/settings.json → log_hook.py (Air)
             ~/.claude/settings.json → log_hook.py (Mini)
statusLine  : saves full session JSON to ~/.cld/status.json (both machines)
```

---

## Security Rules

```
Never hardcode API keys
Read CLD_GAS_URL from ~/yamane/.env always
log_hook.py must be silent (no stdout) — errors to ~/.cld/hook.log only
Verify .env not staged before every commit: git status
```

---

## Pricing Constants

```python
PRO_MONTHLY_USD = 20.00
MODELS = {
    "claude-sonnet-4-20250514": {"input": 3.00,  "output": 15.00},
    "claude-opus-4-20250514":   {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5-20251001":{"input": 1.00,  "output": 5.00},
    "claude-sonnet-4-6":        {"input": 3.00,  "output": 15.00},
}
# cost_pct = (tokens_in * input_ppm + tokens_out * output_ppm) / (20 * 1_000_000) * 100
```

---

## Lessons

```
[GAS-1]  Always -L in curl — GAS redirects before responding
[GAS-2]  Redeploy = New version — /dev URL is unstable
[GAS-3]  Cold start 10-20s — Python timeout must be >= 30s
[GAS-9]  ES5 only in .gs files — no arrow functions, no const/let
[GAS-10] Test with ping first always

[HOOK-1] log_hook.py reads stdin JSON from Claude Code
[HOOK-2] Must exit silently — any stdout breaks Claude Code display
[HOOK-3] All errors go to ~/.cld/hook.log

[DAEMON-1] Poll Safari first, then Chrome
[DAEMON-2] Idle > 30min = new session (don't merge)
[DAEMON-3] Write PID to ~/.cld/daemon.pid for clean stop

[STATUSLINE-1] statusLine JSON has real rate_limits.five_hour, seven_day, context_window, cost.total_cost_usd
[STATUSLINE-2] Save to ~/.cld/status.json — primary data source for TUI
[STATUSLINE-3] Air: add save to settings.json statusLine command
               Mini: patch ~/.claude/statusline-command.sh after input=$(cat) line
[TUI-1] screen=False + expand=False + \033[8;5;85t = compact 85×5 auto-resize
```
