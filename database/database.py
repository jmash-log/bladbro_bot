"""Database layer — talks to Supabase (Postgres) instead of SQLite."""
import os
from datetime import date
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    """Open a connection to Postgres."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Create the tables if they don't exist."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS periods (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    start_date DATE NOT NULL,
                    end_date DATE,
                    UNIQUE (user_id, start_date)
                );
            """)
        conn.commit()


def get_or_create_user(name):
    """Get the user by name, creating them if needed. Returns the id."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE name = %s", (name,))
            row = cur.fetchone()
            if row:
                return row["id"]
            cur.execute(
                "INSERT INTO users (name) VALUES (%s) RETURNING id",
                (name,),
            )
            user_id = cur.fetchone()["id"]
        conn.commit()
        return user_id


def add_period(user_id, start_date):
    """Log a period start."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO periods (user_id, start_date)
                VALUES (%s, %s)
                ON CONFLICT (user_id, start_date) DO NOTHING
                """,
                (user_id, start_date),
            )
        conn.commit()


def update_period_end(user_id, period_id, end_date):
    """Set the end date for a period."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE periods SET end_date = %s WHERE id = %s AND user_id = %s",
                (end_date, period_id, user_id),
            )
        conn.commit()


def get_periods(user_id):
    """All periods for a user, oldest first."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, start_date, end_date
                FROM periods
                WHERE user_id = %s
                ORDER BY start_date ASC
                """,
                (user_id,),
            )
            rows = cur.fetchall()
    return [
        {
            "id": row["id"],
            "start_date": row["start_date"].isoformat(),
            "end_date": row["end_date"].isoformat() if row["end_date"] else None,
        }
        for row in rows
    ]


def get_last_period(user_id):
    """The most recent period."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, start_date, end_date
                FROM periods
                WHERE user_id = %s
                ORDER BY start_date DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
            "start_date": row["start_date"].isoformat(),
            "end_date": row["end_date"].isoformat() if row["end_date"] else None,
    }
