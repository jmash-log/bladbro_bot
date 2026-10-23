"""Cycle Companion — terminal chat (Phase 3).

Periods now save to SQLite. The CSV is only a one-time seed.
"""
from datetime import date

from cycle.calculator import calculate_cycle_lengths, current_cycle_day
from cycle.statistics import calculate_statistics
from cycle.predictor import predict_next_period
from cycle.phases import estimate_phase

from chat.parser import parse_message
from chat.responses import (
    next_period_response,
    status_response,
    stats_response,
    history_response,
    unknown_response,
    serious_response,
    safety_check,
    late_response,
)

from database import database as db


def load_engine():
    """Set up the database and load everything from it."""
    db.init_db()
    user_id = db.get_or_create_user("Ash")

    # Seed once from the CSV if the DB is empty.
    if not db.get_periods(user_id):
        db.seed_from_csv(user_id, "data/historical_cycles.csv")

    return user_id


def handle(intent, user_id, stats, last_start, count=5):
    """Route an intent to the right response."""
    if intent == "START_PERIOD":
        # Close any open period first, then start a new one.
        open_period = db.get_last_period(user_id)
        if open_period and not open_period["end_date"]:
            db.update_period_end(user_id, open_period["id"], date.today())
        db.add_period(user_id, date.today())
        return "Logged. Period started today."

    if intent == "END_PERIOD":
        open_period = db.get_last_period(user_id)
        if open_period and not open_period["end_date"]:
            db.update_period_end(user_id, open_period["id"], date.today())
            return "Logged. Period ended today."
        return "No open period to close."

    if intent == "NEXT_PERIOD":
        periods = db.get_periods(user_id)
        lengths = calculate_cycle_lengths(periods)
        prediction = predict_next_period(lengths, last_start)
        return next_period_response(prediction)

    if intent == "STATUS":
        cycle_day = current_cycle_day(last_start)
        typical = stats["weighted_median"] if stats else None
        phase_info = estimate_phase(cycle_day, typical)
        return status_response(cycle_day, phase_info, last_start)

    if intent == "STATS":
        return stats_response(stats)

    if intent == "HISTORY":
        return history_response(db.get_periods(user_id), limit=count)

        periods = db.get_periods(user_id)
        lengths = calculate_cycle_lengths(periods)
        prediction = predict_next_period(lengths, last_start)
        return late_response(prediction, date.today())

    return unknown_response()


def main():
    user_id = load_engine()

    # Compute stats once for the session.
    periods = db.get_periods(user_id)
    lengths = calculate_cycle_lengths(periods)
    stats = calculate_statistics(lengths)
    last_start = periods[-1]["start_date"] if periods else None
    last_start = date.fromisoformat(last_start) if last_start else None

    print("Cycle Companion (database connected). Type 'quit' to exit.")

    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if text.lower() in ("quit", "exit"):
            print("Bye.")
            break

        if not text:
            continue

        if safety_check(text):
            print(serious_response())
            continue

        parsed = parse_message(text)
        print(handle(parsed["intent"], user_id, stats, last_start, parsed.get("count", 5)))


if __name__ == "__main__":
    main()
