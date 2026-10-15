"""Chapter 3 — a metric with no variance has no power.

A grader that returns 5.00 with zero variance is not telling you the quality is
excellent. It is telling you nothing at all, and it will keep telling you
nothing for as long as you keep shipping against it.

Here two arms differ substantially in real quality. A saturated 1-5 grader
cannot see it. A ground-truth-anchored coverage metric, computed over the same
cases, sees it immediately.

The diagnostic is available *before* you run any comparison: look at the
distribution, not the mean. Zero spread means zero discriminative power.

Run it:  python3 demos/ch3_zero_variance_is_zero_signal.py
"""
from __future__ import annotations

import random
import statistics

N = 200
CHECKLIST = 5          # acceptance criteria attached to each case


def latent_quality(center: float, rng: random.Random) -> float:
    return max(0.0, min(1.0, rng.gauss(center, 0.18)))


def saturated_grader(q: float) -> int:
    """A 1-5 'readability' rubric. Almost everything is readable, so almost
    everything scores 5. This is what a ceiling looks like from the inside."""
    return 5 if q > 0.12 else 4


def coverage_metric(q: float, rng: random.Random) -> float:
    """Fraction of this case's own acceptance criteria that were met."""
    return sum(1 for _ in range(CHECKLIST) if rng.random() < q) / CHECKLIST


def permutation_p(a: list[float], b: list[float], rng: random.Random,
                  iters: int = 20_000) -> float:
    obs = abs(statistics.mean(b) - statistics.mean(a))
    pool = a + b
    n = len(a)
    hits = 0
    for _ in range(iters):
        rng.shuffle(pool)
        if abs(statistics.mean(pool[n:]) - statistics.mean(pool[:n])) >= obs:
            hits += 1
    return (hits + 1) / (iters + 1)


def main() -> None:
    rng = random.Random(11)
    qa = [latent_quality(0.55, rng) for _ in range(N)]
    qb = [latent_quality(0.75, rng) for _ in range(N)]

    rows = []
    for label, metric in (
        ("readability 1-5 (saturated)", lambda q: float(saturated_grader(q))),
        ("requirements-coverage 0..1", lambda q: coverage_metric(q, rng)),
    ):
        a = [metric(q) for q in qa]
        b = [metric(q) for q in qb]
        rows.append((label, a, b))

    print(f"{'metric':<30}{'arm A':>9}{'arm B':>9}{'delta':>9}"
          f"{'sd(A)':>8}{'p':>9}")
    print("-" * 74)
    for label, a, b in rows:
        p = permutation_p(list(a), list(b), random.Random(3))
        print(f"{label:<30}{statistics.mean(a):>9.3f}{statistics.mean(b):>9.3f}"
              f"{statistics.mean(b)-statistics.mean(a):>+9.3f}"
              f"{statistics.pstdev(a):>8.3f}{p:>9.4f}")

    sat = rows[0][1]
    print()
    print("the distribution nobody plotted")
    print("-" * 74)
    for v in sorted(set(sat)):
        k = sat.count(v)
        print(f"  score {v:.0f}: {'#' * (k * 50 // len(sat)):<50} {k}/{len(sat)}")
    print()
    print("the rule")
    print("-" * 74)
    print("  Check the spread of a metric before you trust any comparison made")
    print("  with it. A grader pinned at the ceiling will report 'no")
    print("  regression' forever — including on the release that breaks.")
    print("  The fix is not a better prompt for the same rubric. It is a")
    print("  different measurement: anchor to per-case acceptance criteria and")
    print("  score the fraction met, so the metric has somewhere to move.")


if __name__ == "__main__":
    main()
