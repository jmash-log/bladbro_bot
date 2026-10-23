"""One-time script: load historical cycles from CSV into Supabase."""
import os
import csv
from datetime import date
from dotenv import load_dotenv
from database import database as db

load_dotenv()

CSV_FILE = "historical_cycles.csv"


def main():
    db.init_db()
    user_id = db.get_or_create_user("Ash")

    with open(CSV_FILE) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    count = 0
    for row in rows:
        start = date.fromisoformat(row["period_start"])
        end_raw = row["period_end"].strip()
        end = date.fromisoformat(end_raw) if end_raw else None

        db.add_period(user_id, start)
        if end:
            last = db.get_last_period(user_id)
            db.update_period_end(user_id, last["id"], end)
        count += 1

    print(f"Seeded {count} periods for user {user_id}.")


if __name__ == "__main__":
    main()
