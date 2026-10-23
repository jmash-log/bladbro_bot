"""Cycle Companion — quick test / local brain.

Run this to see your statistics, next-period window, and
current phase, all from your real data.
"""
from datetime import date

from cycle.calculator import load_cycles, calculate_cycle_lengths
from cycle.statistics import calculate_statistics
from cycle.predictor import predict_next_period
from cycle.phases import estimate_phase


def main():
    # 1. Load your real data
    cycles = load_cycles("data/historical_cycles.csv")

    # 2. Compute cycle lengths (gap between consecutive starts)
    lengths = calculate_cycle_lengths(cycles)

    # 3. Your personal statistics
    print("=== STATISTICS ===")
    stats = calculate_statistics(lengths)
    print(stats)
    print()

    # 4. Next-period prediction (window, not a date)
    print("=== NEXT PERIOD ===")
    last_start = cycles[-1]["start"]  # most recent period start
    prediction = predict_next_period(lengths, last_start)
    print(prediction)
    print()

    # 5. Current phase estimate
    print("=== CURRENT PHASE ===")
    today = date.today()
    cycle_day = (today - last_start).days + 1
    typical = stats["weighted_median"] if stats else None
    print(estimate_phase(cycle_day, typical))


if __name__ == "__main__":
    main()
