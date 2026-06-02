import sqlite3
import os
from datetime import date, datetime, timedelta
from config import DB_PATH, CLD_DIR


def _conn():
    os.makedirs(CLD_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id           TEXT PRIMARY KEY,
                timestamp    TEXT NOT NULL,
                source       TEXT NOT NULL,
                model        TEXT DEFAULT '',
                project      TEXT DEFAULT '',
                task         TEXT DEFAULT '',
                category     TEXT DEFAULT 'other',
                tokens_in    INTEGER DEFAULT 0,
                tokens_out   INTEGER DEFAULT 0,
                cost_pct     REAL DEFAULT 0.0,
                duration_min INTEGER DEFAULT 0,
                synced       INTEGER DEFAULT 0
            )
        """)


def insert_session(s):
    with _conn() as c:
        c.execute("""
            INSERT INTO sessions
                (id, timestamp, source, model, project, task, category,
                 tokens_in, tokens_out, cost_pct, duration_min, synced)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                model=excluded.model,
                project=excluded.project,
                task=excluded.task,
                category=excluded.category,
                tokens_in=excluded.tokens_in,
                tokens_out=excluded.tokens_out,
                cost_pct=excluded.cost_pct,
                duration_min=excluded.duration_min
        """, (
            s['id'], s['timestamp'], s.get('source', 'code'),
            s.get('model', ''), s.get('project', ''), s.get('task', ''),
            s.get('category', 'other'), s.get('tokens_in', 0),
            s.get('tokens_out', 0), s.get('cost_pct', 0.0),
            s.get('duration_min', 0), s.get('synced', 0),
        ))


def _to_dicts(rows, cursor):
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]


def get_today():
    today = date.today().isoformat()
    with _conn() as c:
        cur = c.execute(
            "SELECT * FROM sessions WHERE date(timestamp)=? ORDER BY timestamp DESC",
            (today,)
        )
        return _to_dicts(cur.fetchall(), cur)


def get_week():
    with _conn() as c:
        cur = c.execute(
            "SELECT * FROM sessions WHERE date(timestamp)>=date('now','-6 days') ORDER BY timestamp DESC"
        )
        return _to_dicts(cur.fetchall(), cur)


def get_month():
    with _conn() as c:
        cur = c.execute(
            "SELECT * FROM sessions WHERE date(timestamp)>=date('now','start of month') ORDER BY timestamp DESC"
        )
        return _to_dicts(cur.fetchall(), cur)


def get_recent_hours(n=5):
    cutoff = (datetime.now() - timedelta(hours=n)).isoformat()
    with _conn() as c:
        cur = c.execute(
            "SELECT * FROM sessions WHERE timestamp >= ? ORDER BY timestamp DESC",
            (cutoff,)
        )
        return _to_dicts(cur.fetchall(), cur)


def get_unsynced():
    with _conn() as c:
        cur = c.execute("SELECT * FROM sessions WHERE synced=0")
        return _to_dicts(cur.fetchall(), cur)


def mark_synced(ids):
    if not ids:
        return
    with _conn() as c:
        placeholders = ','.join('?' * len(ids))
        c.execute(f"UPDATE sessions SET synced=1 WHERE id IN ({placeholders})", ids)
