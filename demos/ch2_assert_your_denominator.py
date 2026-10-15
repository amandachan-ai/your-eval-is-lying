"""Chapter 2 — assert your denominator.

Your judge shares an API quota with production traffic. Under load some calls
come back rate-limited, the harness records "no score", and the analysis skips
those rows. Coverage drops and nobody notices, because the report prints a mean.

Chapter 1's loss correlated with *content*. This one correlates with *time* —
and that is worse than it sounds, because **eval suites are almost always
ordered**. Tasks are grouped by category. So a contiguous outage does not
remove a random sample; it removes whole categories.

Run it:  python3 demos/ch2_assert_your_denominator.py
"""
from __future__ import annotations

import random
import statistics

CATEGORIES = [
    ("summarize", 4.4),      # easy for the model
    ("multi_turn", 2.6),     # hard
    ("tool_use", 2.9),       # hard
    ("rewrite", 4.2),        # easy
]
PER_CATEGORY = 24


def run_suite(rng: random.Random) -> list[tuple[str, float | None]]:
    """Tasks execute in suite order. A quota outage hits a contiguous window."""
    tasks = [(name, base) for name, base in CATEGORIES for _ in range(PER_CATEGORY)]
    outage = range(20, 62)            # 429s from task 20 to task 61
    rows: list[tuple[str, float | None]] = []
    for i, (name, base) in enumerate(tasks):
        score = max(1.0, min(5.0, rng.gauss(base, 0.6)))
        rows.append((name, None if i in outage else score))
    return rows


def main() -> None:
    rows = run_suite(random.Random(7))
    scored = [(c, s) for c, s in rows if s is not None]

    print("what the report printed")
    print("-" * 52)
    print(f"  overall mean: {statistics.mean(s for _, s in scored):.2f} / 5")
    print()

    print("what it should have printed")
    print("-" * 52)
    print(f"  {'category':<12}{'scored':>8}{'expected':>10}{'mean':>8}")
    for name, _ in CATEGORIES:
        got = [s for c, s in scored if c == name]
        flag = "" if len(got) == PER_CATEGORY else "   ← INCOMPLETE"
        mean = f"{statistics.mean(got):.2f}" if got else "  n/a"
        print(f"  {name:<12}{len(got):>8}{PER_CATEGORY:>10}{mean:>8}{flag}")
    n, total = len(scored), len(rows)
    print(f"  {'TOTAL':<12}{n:>8}{total:>10}   coverage {n/total:.0%}")
    print()

    full = [statistics.mean(
        [s for c, s in scored if c == name] or [0]) for name, _ in CATEGORIES]
    true_mean = statistics.mean(base for _, base in CATEGORIES)
    print(f"  the two hard categories are the ones that got wiped, so the")
    print(f"  reported mean ({statistics.mean(s for _, s in scored):.2f}) sits well above the true")
    print(f"  suite average (~{true_mean:.2f}). Quality did not improve. Coverage fell.")
    print()
    print("the rule")
    print("-" * 52)
    print("  A mean without a denominator is not a result.")
    print("  Assert coverage per category BEFORE reporting, and fail the run")
    print("  when it is short. An eval that silently measures whatever")
    print("  survived is measuring the outage, not the model.")


if __name__ == "__main__":
    main()
