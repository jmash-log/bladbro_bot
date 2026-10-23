"""SQLite database layer for Cycle Companion.

Everything that touches the database lives here. The rest of
the app never writes SQL directly — it calls these functions.
"""
import sqlite3
from datetime import date, datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "cycle_companion.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection():
    """Open a connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist. Safe to call every start."""
    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def get_or_create_user(name="Ash"):
    """Return the user id, creating the user if needed."""
    conn = get_connection()
    row = conn.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
    if row:
        user_id = row["id"]
    else:
        cur = conn.execute("INSERT INTO users (name) VALUES (?)", (name,))
        user_id = cur.lastrowid
        conn.commit()
    conn.close()
    return user_id


# ---------- Periods ----------

def add_period(user_id, start_date, end_date=None, status="confirmed", source="manual"):
    """Insert a period. start_date is a date object or 'YYYY-MM-DD' string."""
    if isinstance(start_date, date):
        start_date = start_date.isoformat()
    if end_date is not None and isinstance(end_date, date):
        end_date = end_date.isoformat()

    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO periods (user_id, start_date, end_date, status, source) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, start_date, end_date, status, source),
    )
    conn.commit()
    period_id = cur.lastrowid
    conn.close()
    return period_id


def get_periods(user_id):
    """All periods, oldest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM periods WHERE user_id = ? ORDER BY start_date",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_last_period(user_id):
    """Most recent period, or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM periods WHERE user_id = ? ORDER BY start_date DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_period_end(user_id, period_id, end_date):
    """Set the end date on an open period."""
    if isinstance(end_date, date):
        end_date = end_date.isoformat()
    conn = get_connection()
    conn.execute(
        "UPDATE periods SET end_date = ? WHERE id = ? AND user_id = ?",
        (end_date, period_id, user_id),
    )
    conn.commit()
    conn.close()


# ---------- Cycle gaps ----------

def add_cycle_gap(user_id, prev_start, next_start, gap_days, status="uncertain"):
    """Record a suspicious gap for later review."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO cycle_gaps (user_id, prev_start, next_start, gap_days, status) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, prev_start.isoformat(), next_start.isoformat(), gap_days, status),
    )
    conn.commit()
    conn.close()


def get_cycle_gaps(user_id):
    """All flagged gaps."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM cycle_gaps WHERE user_id = ? ORDER BY next_start",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- Symptoms ----------

def add_symptom(user_id, symptom_date, symptom, severity=None):
    """Log a symptom for a given date."""
    if isinstance(symptom_date, date):
        symptom_date = symptom_date.isoformat()
    conn = get_connection()
    conn.execute(
        "INSERT INTO symptoms (user_id, date, symptom, severity) VALUES (?, ?, ?, ?)",
        (user_id, symptom_date, symptom, severity),
    )
    conn.commit()
    conn.close()


# ---------- Seed from CSV ----------

def seed_from_csv(user_id, csv_path):
    """Import periods from the historical CSV on first run.

    Skips rows that already exist (idempotent).
    """
    import csv as csv_mod

    conn = get_connection()
    existing = {r["start_date"] for r in conn.execute(
        "SELECT start_date FROM periods WHERE user_id = ?", (user_id,)
    )}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv_mod.DictReader(f)
        for row in reader:
            start = row["period_start"]
            if start in existing:
                continue
            status = row.get("status", "confirmed")
            conn.execute(
                "INSERT INTO periods (user_id, start_date, end_date, status, source) "
                "VALUES (?, ?, ?, ?, 'backfill')",
                (user_id, start, row["period_end"], status),
            )
    conn.commit()
    conn.close()
