# Your eval is lying to you

**A field guide to the failure modes of measurement itself, when what you are
measuring is a language model.**

Most writing about LLM evaluation is about what to measure. This is about
whether your instrument works — because almost every serious mistake I have seen in
LLM evaluation was not a wrong conclusion drawn from good numbers. It was a broken instrument producing numbers that looked fine.

That is the uncomfortable part. A wrong conclusion announces itself eventually;
someone disagrees, someone reruns it. **A broken instrument produces a report
with a plausible mean, a clean-looking distribution, and a confident p-value,
and nobody has any reason to look twice.**

Every chapter here is one way that happens, with a runnable demonstration you
can check in under a minute.

```bash
git clone https://github.com/amandachan-ai/your-eval-is-lying
cd your-eval-is-lying
python3 demos/ch1_silent_sample_loss.py        # standard library only, no deps
```

---

## Part I — The instrument fails silently

### 1. Non-random sample loss

A parser strips backslashes before `json.loads`, so any judge explanation that
quotes the source text fails to parse. The exception is caught, the row is
skipped, the run reports a mean over whatever survived.

Losing samples is not the problem. **Losing them non-randomly is.** Judges quote
the text when they are justifying a low score — so the survivors are the cases
the model handled well.

```
                 n    mean   ← what the run reported
control        127    4.24
treatment      137    4.36
                     +0.11   ← measured effect

                 n    mean   ← after fixing the parser
control        200    3.27
treatment      200    3.46
                     +0.19   ← true effect
```

The mean is inflated by a full point, the measured effect is 58% of the real
one, and the two arms were not even scored on comparable samples. Nothing in the
report says so. The only symptom is a row count nobody looked at.

→ [`demos/ch1_silent_sample_loss.py`](demos/ch1_silent_sample_loss.py)

**The rule:** count your rows, every run, and compare the count to what you
submitted. A `try/except` around a parser is a place where data goes to die
quietly.

---

### 2. Assert your denominator

Your judge shares an API quota with production traffic. Under load some calls
come back rate-limited, the harness records "no score", the analysis skips those
rows.

Chapter 1's loss correlated with *content*. This one correlates with *time* —
and that is worse than it sounds, because **eval suites are almost always
ordered**. Tasks are grouped by category. So a contiguous outage does not remove
a random sample. It removes whole categories.

```
what the report printed
  overall mean: 3.95 / 5

what it should have printed
  category      scored  expected    mean
  summarize         20        24    4.32   ← INCOMPLETE
  multi_turn         0        24     n/a   ← INCOMPLETE
  tool_use          10        24    2.71   ← INCOMPLETE
  rewrite           24        24    4.16
  TOTAL             54        96   coverage 56%
```

The two hard categories are the ones that got wiped. The reported mean sits well
above the suite's true average. Quality did not improve; coverage fell.

→ [`demos/ch2_assert_your_denominator.py`](demos/ch2_assert_your_denominator.py)

**The rule:** a mean without a denominator is not a result. Assert coverage per
category before reporting, and fail the run when it is short. Give evaluation
its own quota — sharing one with production means your measurement degrades
exactly when the system is under the load you most wanted to measure.

---

### 3. Zero variance is zero signal

A grader that returns 5.00 with no spread is not telling you the quality is
excellent. It is telling you nothing, and it will keep telling you nothing for
as long as you keep shipping against it.

Two arms, a real and substantial difference in quality, the same underlying
cases, two metrics:

```
metric                            arm A    arm B    delta   sd(A)        p
readability 1-5 (saturated)       4.995    5.000   +0.005   0.071   1.0000
requirements-coverage 0..1        0.596    0.738   +0.142   0.253   0.0000

the distribution nobody plotted
  score 4:                                                    1/200
  score 5: #################################################  199/200
```

→ [`demos/ch3_zero_variance_is_zero_signal.py`](demos/ch3_zero_variance_is_zero_signal.py)

**The rule:** check the spread before you trust any comparison made with the
metric. A grader pinned at the ceiling reports "no regression" forever —
including on the release that breaks. The fix is not a better prompt for the
same rubric; it is a different measurement. Anchor to per-case acceptance
criteria and score the fraction met, so the metric has somewhere to move.

---

## Coming

**Part II — The estimator is the experiment**
4. Pick the estimand before the statistic — majority vote over replicates erases
   intermittent harm, and if the arms carry different amounts of it, the
   estimator is biased before you compute anything. Users do not vote; they
   sample once.
5. Equivalence is not the absence of difference — `p > 0.05` does not mean "no
   regression". Declare a bound first, then run TOST.
6. The A/A control — how do you know ±0.07 is not real? Run the thing against
   itself and find out where your noise floor is.

**Part III — When the judge cannot be trusted**
7. Find a judge-free observable — when a property is lexically or structurally
   decidable, measure it directly instead of asking a model about it.
8. Deterministic detectors — cheap, reproducible, zero variance, and they catch
   the defects a rubric was never going to name.

**Part IV — Discipline**
9. **Preregister the escape hatch too.** The chapter I least want to write. A
   preregistered gate you reinterpret after seeing the result is not a gate, and
   the fact that your post-hoc analysis was *correct* does not repair it.
10. The evidence budget — decide what the decision is worth before you design
    the evaluation. If every branch leads to the same action, do not run it.
11. Corpus ceilings — when label capture is low and label noise is high, raw
    user feedback is not a gold standard, and treating it as one quietly caps
    everything downstream.

---

## About the examples

Every demonstration here is **synthetic and self-contained** — a few dozen lines
of standard-library Python that construct the failure and show you its shape.
Nothing in this repository contains or depends on any employer's data, code,
metrics, or internal tooling.

That is not only a precaution. It is what makes the claims checkable: you can
run each one, change the parameters, and watch the failure appear and disappear.
A playbook you have to take on faith is worth much less than one you can break.

## License

MIT
