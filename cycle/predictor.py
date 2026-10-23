"""Predict the next period as a WINDOW, never a fake exact date.

Design rules from the spec:
  - No hard-coded 28 days.
  - Recent cycles weigh more than old ones.
  - Output is a range + confidence + the reasoning behind it.
  - If there isn't enough data, say so instead of guessing.
"""
from datetime import timedelta
from .statistics import calculate_statistics


def predict_next_period(cycle_lengths, last_period_start, recent_count=12):
    """Predict when the next period will start.

    cycle_lengths: list of dicts with 'length' and 'start',
                   as produced by calculate_cycle_lengths().
    last_period_start: date of the most recent period start.
    Returns a dict with a window, confidence, and basis.
    """
    stats = calculate_statistics(cycle_lengths, recent_count)

    if stats is None or stats["count"] < 3:
        return {
            "predicted_start": None,
            "window_start": None,
            "window_end": None,
            "confidence": "insufficient_data",
            "basis": {
                "reason": "Not enough confirmed cycles to predict.",
                "sample_size": stats["count"] if stats else 0,
            },
        }

    # The centre of our prediction: the weighted median.
    centre_length = stats["weighted_median"]

    # How wide the window is: driven by variability (MAD) and
    # sample size. Small sample => wider window, honestly.
    variability = stats["recent_mad"] if stats["recent_count"] >= 6 else stats["mad"]
    sample_size = stats["count"]

    # Window half-width: MAD gives the typical spread. We widen a
    # bit for small samples, and add a small safety margin.
    half_width = max(1, round(variability * 1.25))
    if sample_size < 10:
        half_width += 1  # less data => wider honest window

    predicted_start = last_period_start + timedelta(days=centre_length)
    window_start = predicted_start - timedelta(days=half_width)
    window_end = predicted_start + timedelta(days=half_width)

    # Confidence: how tight the pattern is relative to the window.
    if variability <= 1.5 and sample_size >= 10:
        confidence = "high"
    elif variability <= 3:
        confidence = "moderate"
    else:
        confidence = "low"

    return {
        "predicted_start": predicted_start,
        "window_start": window_start,
        "window_end": window_end,
        "confidence": confidence,
        "basis": {
            "typical_cycle": centre_length,
            "variability": variability,
            "sample_size": sample_size,
        },
    }
