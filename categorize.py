KEYWORDS = {
    "debug":   ["fix", "bug", "error", "broken", "issue", "crash", "debug"],
    "plan":    ["plan", "spec", "design", "brainstorm", "think", "review"],
    "feature": ["build", "add", "create", "implement", "new", "develop"],
    "config":  ["setup", "install", "config", "deploy", "cron", "env"],
    "update":  ["update", "clean", "refactor", "improve", "migrate"],
}


def categorize(task: str) -> str:
    lower = task.lower()
    for cat, kws in KEYWORDS.items():
        for kw in kws:
            if kw in lower:
                return cat
    return "other"
