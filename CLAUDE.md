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
```

---

## Git Workflow

```
Air = workstation (develop + test)
Flow: edit → git add -A → git commit → git push

Init (first time):
  cd ~/claude-db
  git init
  git remote add origin [repo-url]
  git add -A && git commit -m "initial"
```

## Drive Backup

```
Folder   : /AI-Context/claude-db/
Parent ID: (new folder — create if not exist)
Files    : weekly-YYYY-WW.md, working logs
Pattern  : same as yamane — upload via Google Drive MCP
```

## Working Log Triggers

```
start/cont  → load Drive context first
finish/done → generate working log → upload Drive → git commit
log         → show current log
```

---

## GAS — Claude Dashboard Project

```
GAS Project : "Claude Dashboard" (separate from Yamane)
env key     : CLD_GAS_URL (in ~/yamane/.env)
Sheet key   : CLD_SHEET_ID (in ~/yamane/.env)
Actions     : saveClaudeLog, getClaudeLogs, ping
```

### Deploy pattern (same as Yamane)
```
Execute as    : Me (her.alfa185@gmail.com)
Who has access: Anyone
URL format    : https://script.google.com/macros/s/[ID]/exec
Always use /exec — never /dev
Always -L flag in curl
Redeploy = New version every time code changes
```

### Test after deploy
```bash
curl -s -L -X POST "$(grep CLD_GAS_URL ~/yamane/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"action":"ping"}'
# expect: {"ok":true,"ts":"..."}
```

---

## GAS Standard Rules (critical)

```
ES5 only — no const/let, no =>, no fetch(), no template literals
appendRow() for single rows
getDataRange().getValues() for reading — never loop getValue()
Max execution: 30s
Timeout Python side: 30s minimum
```

---

## Storage

```
Local  : ~/.cld/sessions.db (SQLite)
Remote : GAS → Google Sheets LOG tab → Drive /AI-Context/claude-db/
Sync   : clduse sync (manual) or auto on session end
```

---

## Services & Ports

```
clduse TUI      : terminal only (no port)
daemon          : background process, PID in ~/.cld/daemon.pid
Claude Code hook: ~/.claude/settings.json Stop hook → log_hook.py
```

---

## Key Paths

```
~/claude-db/       project root
~/.cld/sessions.db        SQLite runtime data
~/.cld/daemon.pid         daemon PID
~/.cld/daemon.log         daemon log
~/.cld/hook.log           Stop hook log (errors only)
~/.claude/settings.json   Claude Code hooks config
~/yamane/.env             all env keys including CLD_GAS_URL
~/claude-db/gas/   GAS source files (paste into script.google.com)
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

## Lessons (relevant to this project)

```
[GAS-1] Always -L in curl — GAS redirects before responding
[GAS-2] Redeploy = New version — /dev URL is unstable
[GAS-3] Cold start 10-20s — Python timeout must be >= 30s
[GAS-4] SHEET_ID in Sheets URL: /spreadsheets/d/[SHEET_ID]/edit
[GAS-9] ES5 only in .gs files — no arrow functions, no const/let
[GAS-10] Test with ping first always

[HOOK-1] log_hook.py reads stdin JSON from Claude Code
[HOOK-2] Must exit silently — any stdout breaks Claude Code display
[HOOK-3] All errors go to ~/.cld/hook.log

[DAEMON-1] Poll Safari first, then Chrome — user may use either
[DAEMON-2] Idle > 30min = new session (don't merge)
[DAEMON-3] Write PID to ~/.cld/daemon.pid for clean stop
```
