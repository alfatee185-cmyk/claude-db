# clduse — Manual

CLI dashboard to monitor Claude Code + Claude.ai usage.
Tracks sessions locally in SQLite, syncs to Google Sheets via GAS.

---

## Launch

```bash
clduse          # live dashboard (Ctrl+C to exit)
```

The dashboard auto-refreshes every 5s showing:
- **LIVE**: current session context window %, model, project (reads ~/.claude/projects live)
- **Session / 5hr / Week / Month**: cumulative cost % of $20/mo Pro plan
- **Code / Web**: split between Claude Code sessions and Claude.ai browser sessions
- **TODAY LOG**: last 6 sessions with task labels and cost%

> Note: Session% and context% update live from the active JSONL.
> Cost% for past sessions updates when a session ends (Stop hook).

---

## Commands

Run in a **separate terminal** while clduse is open, or standalone:

### Label a session
```bash
clduse log "task description"
```
Labels the latest today session. Auto-categorizes:
- `debug`   — fix, bug, error, broken, issue, crash, debug
- `plan`    — plan, spec, design, brainstorm, think, review
- `feature` — build, add, create, implement, new, develop
- `config`  — setup, install, config, deploy, cron, env
- `update`  — update, clean, refactor, improve, migrate

### Sync to Google Sheets
```bash
clduse sync            # push new (unsynced) sessions
clduse resync today    # re-push all today sessions (use after labeling)
clduse resync week     # re-push all this week
clduse resync month    # re-push all this month
```

### Session views
```bash
clduse today    # detailed session table (debug) — tokens, model, project
clduse week     # weekly analysis + category breakdown + heatmap
```

### Scan historical sessions
```bash
clduse scan     # re-reads ~/.claude/projects/**/*.jsonl into SQLite
```

### Daemon (Claude.ai browser tracking)
```bash
clduse daemon status   # check if running
clduse daemon start    # start background poller
clduse daemon stop     # stop
```
The daemon polls Safari/Chrome every 30s via AppleScript.
Saves a web session to SQLite when you leave claude.ai.
Idle > 30min on same page = new session.

---

## Key paths

```
~/claude-db/              project root
~/.cld/sessions.db        SQLite — all sessions
~/.cld/daemon.pid         daemon PID
~/.cld/daemon.log         daemon log
~/.cld/hook.log           Stop hook errors
~/.claude/settings.json   Stop hook config
~/yamane/.env             CLD_GAS_URL, CLD_SHEET_ID
```

---

## Data flow

```
Claude Code session ends
  → log_hook.py (Stop hook) reads stdin JSON
  → inserts tokens + cost% to sessions.db

Browser on claude.ai
  → daemon polls every 30s (AppleScript)
  → saves session on navigate away, with duration_min

clduse sync / resync
  → POST to GAS (CLD_GAS_URL)
  → GAS appends rows to Google Sheet LOG tab
```

---

## Pricing reference

| Model | Input $/1M | Output $/1M |
|---|---|---|
| claude-sonnet-4-6 / sonnet-4 | $3.00 | $15.00 |
| claude-opus-4 | $15.00 | $75.00 |
| claude-haiku-4-5 | $1.00 | $5.00 |

`cost_pct = cost_usd / $20 * 100`

---

## GAS / Google Sheets

- GAS project: "Claude Dashboard" at script.google.com
- Sheet: LOG tab — Date, Time, Source, Model, Project, Task, Category,
  TokensIn, TokensOut, Cost%, DurationMin, Timestamp
- After editing any `.gs` file: Deploy → Manage → New version → Deploy

---

## LaunchAgent (auto-start daemon on login)

```bash
launchctl load ~/Library/LaunchAgents/clduse.daemon.plist
launchctl unload ~/Library/LaunchAgents/clduse.daemon.plist
```
