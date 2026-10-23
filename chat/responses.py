"""Turn engine output into words, with the personality layer.

Dry, witty, science-aware. Safety always beats humour:
if a message looks serious, we switch to plain factual tone.
"""
from datetime import date, timedelta


def format_date(d):
    """'2026-11-04' -> 'Nov 4'. Accepts date or ISO string."""
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return d.strftime("%b %d").replace(" 0", " ")



def next_period_response(prediction):
    """Prediction dict -> conversational reply."""
    if prediction["confidence"] == "insufficient_data":
        return ("I cannot calculate biological events using vibes alone. "
                "Not enough confirmed cycles yet — log a few more periods.")

    start = format_date(prediction["window_start"])
    end = format_date(prediction["window_end"])

    line = f"Next period window: {start}–{end}."

    if prediction["confidence"] == "high":
        line += " That's a tight window — your cycle is impressively consistent."
    elif prediction["confidence"] == "moderate":
        line += " A bit of spread, but the pattern is readable."
    else:
        line += " Lots of variability here, so treat this as a rough guess."

    basis = prediction["basis"]
    line += (f" (based on a ~{basis['typical_cycle']}-day cycle, "
             f"{basis['sample_size']} samples.)")
    return line


def status_response(cycle_day, phase_info, last_start):
    """Current status -> reply."""
    if phase_info["phase"] == "unknown":
        return ("I don't have enough data to place you in the cycle yet. "
                "Log a few periods first.")

    day = phase_info["cycle_day"]
    phase = phase_info["phase"]

    days_since = (date.today() - last_start).days
    line = (f"Cycle day {day} — {phase}. "
            f"Last period started {format_date(last_start)} "
            f"({days_since} days ago).")

    if "fertile" in phase:
        line += " OVULATION WATCH. Emphasis on estimated. Biology did not sign a contract."
    elif phase == "luteal":
        line += " The biological machinery is winding down toward the next event."
    elif phase == "menstruation":
        line += " THE EVENT HAS BEGUN."

    return line


def stats_response(stats):
    """Stats dict -> reply."""
    if stats is None:
        return "No usable cycle data yet. Log a few periods first."

    return (f"Typical cycle: {stats['median']} days "
            f"(weighted median {stats['weighted_median']}). "
            f"Variability (MAD): {stats['mad']} days. "
            f"Based on {stats['count']} confirmed cycles. "
            f"Recent 12: median {stats['recent_median']}, "
            f"MAD {stats['recent_mad']} — "
            f"{'very stable' if stats['recent_mad'] <= 1 else 'somewhat variable'} lately.")


def history_response(cycles, limit=5):
    """Recent periods -> reply."""
    if not cycles:
        return "No history recorded."

    lines = []
    for c in cycles[-limit:]:
        status = "" if c["status"] == "confirmed" else f" ({c['status']})"
        lines.append(f"{format_date(c['start_date'])} → {format_date(c['end_date'])}{status}")

    return "Recent periods:\n" + "\n".join(lines)


def unknown_response():
    return ("Didn't catch that. Try things like:\n"
            "- 'when's my next period?'\n"
            "- 'status'\n"
            "- 'stats'\n"
            "- 'history'\n"
            "- 'period started'\n"
            "- 'period ended'")


def serious_response():
    return ("That sounds like it could be serious. If you're in severe pain, "
            "bleeding very heavily, or feeling faint, please seek medical "
            "attention. I can't diagnose — but I won't joke about this.")


def safety_check(text):
    """Return True if the message sounds serious enough to go serious-mode."""
    serious = ["severe", "unbearable", "fainting", "fainted", "heavy bleeding",
               "very heavy", "fever", "can't stand", "can't move",
               "emergency", "hospital"]
    return any(word in text.lower() for word in serious)

def late_response(prediction, today):
    """Are we past the predicted window? Honest answer."""
    if prediction["confidence"] == "insufficient_data":
        return ("I don't have enough data to judge 'late'. "
                "Log a few more periods first.")

    window_end = prediction["window_end"]
    days_past = (today - window_end).days

    if days_past < 0:
        return (f"Not late yet. Window closes {format_date(window_end)} — "
                f"still {abs(days_past)} day(s) inside it.")
    elif days_past == 0:
        return (f"Today is the last day of the window ({format_date(window_end)}). "
                "Right on the edge — not late yet.")
    else:
        return (f"You're {days_past} day(s) past the window end "
                f"({format_date(window_end)}). That's late for your pattern. "
                "Could be worth keeping an eye on — or a check-in with a doctor "
                "if it stretches on.")
