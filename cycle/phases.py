"""Estimate where in the cycle you are, from YOUR history.

No hard-coded "day 14 = ovulation". Instead:
  - Ovulation is estimated as roughly cycle_length - 14
    (luteal phase is typically ~14 days).
  - Everything is an ESTIMATE. Biology did not sign a contract.
"""
from datetime import timedelta


def estimate_ovulation_day(typical_cycle_length):
    """Rough ovulation day, based on a ~14 day luteal phase."""
    if not typical_cycle_length or typical_cycle_length < 21:
        return None
    return max(1, typical_cycle_length - 14)


def estimate_phase(cycle_day, typical_cycle_length):
    """Return a phase label + fertile-window estimate.

    cycle_day: current day of the cycle (1 = first day of period).
    typical_cycle_length: your median cycle length.
    """
    if typical_cycle_length is None or typical_cycle_length < 21:
        return {
            "phase": "unknown",
            "note": "Not enough data to estimate a phase.",
        }

    ovulation_day = estimate_ovulation_day(typical_cycle_length)

    # Fertile window: 4 days before to 1 day after estimated ovulation.
    # Day at the edge leans luteal rather than fertile.
    fertile_start = ovulation_day - 4
    fertile_end = ovulation_day + 1

    if cycle_day <= 5:
        phase = "menstruation"
    elif cycle_day < fertile_start:
        phase = "follicular"
    elif cycle_day <= fertile_end:
        phase = "fertile window (estimate)"
    else:
        phase = "luteal"

    return {
        "phase": phase,
        "cycle_day": cycle_day,
        "estimated_ovulation_day": ovulation_day,
        "note": "All phase estimates are approximate, based on your "
                "typical cycle length, not a fixed calendar.",
    }
