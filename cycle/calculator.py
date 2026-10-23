"""Cycle Companion — data loading and basic cycle math.

This is the bottom of the stack. Everything else
(statistics, predictor, phases) reads from what this produces.
"""
from datetime import date, datetime
import csv


def parse_date(value):
    """Turn a 'YYYY-MM-DD' string into a date object."""
    return datetime.strptime(value, "%Y-%m-%d").date()


def load_cycles(filepath):
    """Read the CSV and return a list of cycles.

    Each cycle is a dict:
        {"start": date, "end": date, "status": str}

    Sorted by start date, just in case the file isn't.
    """
    cycles = []

    with open(filepath, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cycles.append({
                "start": parse_date(row["period_start"]),
                "end": parse_date(row["period_end"]),
                "status": row["status"]
            })

    cycles.sort(key=lambda cycle: cycle["start"])

    return cycles


def calculate_cycle_lengths(periods):
    """Work out the gap between each period and the one before it.

    Accepts DB rows (dicts with 'start_date').
    """
    results = []

    for i in range(1, len(periods)):
        previous = periods[i - 1]
        current = periods[i]

        prev_start = previous["start_date"]
        curr_start = current["start_date"]

        # DB stores ISO strings; convert to date objects.
        if isinstance(prev_start, str):
            prev_start = date.fromisoformat(prev_start)
        if isinstance(curr_start, str):
            curr_start = date.fromisoformat(curr_start)

        length = (curr_start - prev_start).days

        results.append({
            "start": curr_start,
            "length": length,
            "from_previous": prev_start,
        })

    return results



def current_cycle_day(last_period_start, today=None):
    """Which day of the cycle are we on?

    Day 1 = the first day of the period.
    """
    if today is None:
        today = date.today()

    return (today - last_period_start).days + 1
