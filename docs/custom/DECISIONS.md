# Decision Journal

One entry per capital-allocation or system decision, written BEFORE execution.
Reviewed at quarterly scaling reviews and the annual policy review (July 1).
The point is calibration: expectations are falsifiable only if dated and written first.

Entry template:

```
## YYYY-MM-DD — <decision>
- Decision: <what, size, instrument>
- Reasoning: <why now; which rule/policy section authorizes it>
- Expectation: <what should be true, by when, to call this right>
- Judge on: <date>
- Outcome (filled later): <what happened; right/wrong/unclear; lesson → learnings/>
```

---

## 2026-07-06 — Adopt barbell portfolio policy
- Decision: 55% SGOV / 35% band-rebalanced sleeve / 10% engine reserve; engine gated to ~Sept 2026.
- Reasoning: docs/custom/plans/portfolio_policy.md (five rules, kill criteria pre-registered).
- Expectation: blended 9–14%/yr over full cycle; worst year > −15%; zero forced liquidations ever.
- Judge on: 2027-07-01 (annual review).
- Outcome: —

## 2026-07-07 — Experiment verdict: instrument-weight optimiser comparison (first Threadripper campaign)
- Decision: NO production change. HRP stays a research flag, not the default.
- Evidence: `results/research_battery/20260707_204230/metrics.csv` (5 variants × 6 windows,
  chapter-15 universe, n=6 instruments). Full-period Sharpe: hrp 0.555 > equal 0.539 >
  shrinkage 0.503 > handcraft 0.491 > fixed-baseline 0.478.
- Why no change despite HRP "winning": (1) spread between best and worst estimated variant
  is ~0.06 SR over 52 years — inside one standard error, not significant without bootstrap
  CIs (gauntlet extension pending); (2) HRP is LAST in the 2020s window (-0.099 Sharpe,
  worst 2020s drawdown) — its full-period win is a 1990s artifact; (3) n=6 instruments
  gives a hierarchical method almost nothing to cluster — real test needs the 50-100
  instrument universe (Norgate gate); (4) equal weights nearly matches everything,
  confirming the prior that allocator choice among sane methods ≈ 0.05 SR at this breadth.
- Side-finding (open question): ALL estimated-weight variants collapse in the 2020s
  (Sharpe 0.09–0.19) while fixed weights hold 0.387 — expanding-window estimation may be
  mis-weighting the recent regime.
- Judge on: re-run after (a) bootstrap-CI battery extension, (b) expanded universe.
- Outcome: —

## 2026-07-07 — IRP reallocation out of 원리금보장 (3.9%)
- Decision: PENDING tax-branch check (W-9 ⇒ PFIC/FBAR advice first; W-8BEN ⇒ proceed).
  Target: qualified TDF up to 100%, or 70% index ETFs (unhedged) + 30% safe assets.
- Reasoning: longest-horizon capital earning lowest return; 3.9% vs ~6–8% expected over 25+ yrs.
- Expectation: IRP CAGR > 3.9% + 1.5pp over any rolling 5-year window.
- Judge on: first 5-year checkpoint 2031-07-01.
- Outcome: —
