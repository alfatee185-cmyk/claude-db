import os

PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.00,  "output": 15.00},
    "claude-opus-4-20250514":   {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5-20251001":{"input": 1.00,  "output": 5.00},
    "claude-sonnet-4-6":        {"input": 3.00,  "output": 15.00},
}

PRO_MONTHLY_USD = 20.00
CLD_DIR = os.path.expanduser("~/.cld")
DB_PATH = os.path.join(CLD_DIR, "sessions.db")
CLAUDE_PROJECTS_DIR = os.path.expanduser("~/.claude/projects")
