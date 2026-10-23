"""Personal cycle statistics: median + MAD, recency-weighted.

Why not mean and standard deviation?
  - One weird long gap (54 or 81 days) drags the mean way off,
    but barely moves the median.
  - Standard deviation is inflated by outliers. MAD is a robust
    measure of variability that ignores the outliers' pull.
  - Recent cycles tell us more than ancient ones, so we weight
    newer data higher.
"""
from statistics import median


def get_valid_cycle_lengths(cycle_lengths):
    """Keep only believable cycle lengths (21-45 days).

    This is a temporary sanity filter, NOT the final design.
    The 54 and 81 day gaps are excluded here but still exist
    in the CSV, marked 'uncertain'.
    """
    return [
        c["length"]
        for c in cycle_lengths
        if 21 <= c["length"] <= 45
    ]


def mad(values):
    """Median Absolute Deviation: how far from the median the
    typical cycle sits. Robust to outliers, unlike stdev."""
    centre = median(values)
    return median([abs(v - centre) for v in values])


def calculate_statistics(cycle_lengths, recent_count=12):
    """Compute robust stats, with recent cycles weighted more.

    Returns a dict, or None if there's no usable data.
    """
    valid = get_valid_cycle_lengths(cycle_lengths)

    if not valid:
        return None

    # Recency weighting: weight each cycle by how recent it is.
    # Older cycles get weight 1, the newest get more.
    # We use the position in the sorted-by-date list as a proxy.
    weights = [1 + (i / max(len(valid) - 1, 1)) for i in range(len(valid))]

    # Weighted median: sort by length, walk until cumulative
    # weight crosses half the total.
    pairs = sorted(zip(valid, weights))
    total_weight = sum(weights)
    half = total_weight / 2
    cumulative = 0
    weighted_median = None
    for length, weight in pairs:
        cumulative += weight
        if cumulative >= half:
            weighted_median = length
            break

    result = {
        "count": len(valid),
        "median": median(valid),
        "weighted_median": weighted_median,
        "minimum": min(valid),
        "maximum": max(valid),
        "mad": round(mad(valid), 2),
    }

    # Recent-only stats, to see if the pattern is tightening.
    recent = valid[-recent_count:]
    result["recent_count"] = len(recent)
    result["recent_median"] = median(recent)
    result["recent_mad"] = round(mad(recent), 2)

    return result
