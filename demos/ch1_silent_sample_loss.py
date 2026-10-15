"""Chapter 1 — non-random sample loss.

A judge returns JSON: {"score": 3, "why": "..."}. The parser strips backslashes
before json.loads, so any explanation that *quotes the source text* fails to
parse. The exception is caught, the row is skipped, and the run reports a clean
mean over whatever survived.

The point is not that you lose samples. It is that **you lose them
non-randomly**: judges quote the text when they are justifying a low score, so
the survivors are the cases the model handled well. The mean goes up. The
comparison between two arms goes wherever the quoting rates take it.

Run it:  python3 demos/ch1_silent_sample_loss.py
"""
from __future__ import annotations

import json
import random
import statistics


def judge_output(score: int, quotes_source: bool) -> str:
    """What the judge actually returns, as a raw string."""
    why = (
        'the draft says \\"we should of done it\\" which is ungrammatical'
        if quotes_source
        else "the draft reads cleanly and keeps the original meaning"
    )
    return '{"score": %d, "why": "%s"}' % (score, why)


def parse_broken(raw: str) -> dict | None:
    """The bug. Stripping backslashes breaks every escaped quote."""
    try:
        return json.loads(raw.replace("\\", ""))
    except Exception:
        return None                      # silently dropped, and nobody counts it


def parse_fixed(raw: str) -> dict | None:
    try:
        return json.loads(raw)
    except Exception:
        return None


def make_arm(n: int, low_score_rate: float, rng: random.Random) -> list[str]:
    """Judges quote the source when they justify a low score — that is the
    correlation that turns lost samples into a biased sample."""
    out = []
    for _ in range(n):
        low = rng.random() < low_score_rate
        score = rng.choice([1, 2]) if low else rng.choice([4, 5])
        quotes = low and rng.random() < 0.85     # low scores get quoted
        out.append(judge_output(score, quotes))
    return out


def summarise(raws: list[str], parser) -> tuple[int, float]:
    rows = [r for r in (parser(x) for x in raws) if r is not None]
    return len(rows), statistics.mean(r["score"] for r in rows)


def main() -> None:
    rng = random.Random(0)
    N = 200

    # Two arms. The treatment genuinely helps: fewer low scores.
    control = make_arm(N, low_score_rate=0.45, rng=rng)
    treatment = make_arm(N, low_score_rate=0.30, rng=rng)

    print(f"{'':<12}{'n':>6}{'mean':>8}   ← what the run reported")
    print("-" * 44)
    for name, arm in (("control", control), ("treatment", treatment)):
        n, m = summarise(arm, parse_broken)
        print(f"{name:<12}{n:>6}{m:>8.2f}")
    n_c, m_c = summarise(control, parse_broken)
    n_t, m_t = summarise(treatment, parse_broken)
    print(f"{'':<12}{'':>6}{m_t - m_c:>+8.2f}   ← measured effect")

    print()
    print(f"{'':<12}{'n':>6}{'mean':>8}   ← after fixing the parser")
    print("-" * 44)
    for name, arm in (("control", control), ("treatment", treatment)):
        n, m = summarise(arm, parse_fixed)
        print(f"{name:<12}{n:>6}{m:>8.2f}")
    N_c, M_c = summarise(control, parse_fixed)
    N_t, M_t = summarise(treatment, parse_fixed)
    print(f"{'':<12}{'':>6}{M_t - M_c:>+8.2f}   ← true effect")

    print()
    print(f"coverage:  control {n_c}/{N} = {n_c/N:.0%}   "
          f"treatment {n_t}/{N} = {n_t/N:.0%}")
    print(f"the measured effect is {abs((m_t-m_c)/(M_t-M_c)):.0%} of the true "
          f"effect, and the two arms were")
    print("not even measured on comparable samples.")
    print()
    print("Nothing in the report says any of this. There is no error, no")
    print("warning, and the means look plausible. The only symptom is a row")
    print("count nobody looked at.")


if __name__ == "__main__":
    main()
