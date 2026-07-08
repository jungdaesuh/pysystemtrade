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
- Outcome (a, 2026-07-07): CONFIRMED not significant. Paired stationary block bootstrap
  (2000 reps, mean block 25d, seed 42, common sample 13,422 days): hrp diff +0.076,
  95% CI [-0.078, +0.237]; every variant's CI straddles zero. Notably `equal` has the
  highest P(beats baseline)=0.874 with the tightest CI — the null keeps winning on
  robustness. Evidence: `results/research_battery/20260707_212812/bootstrap_ci.csv`.
  Verdict stands: no production change; (b) expanded-universe re-test remains open.

## 2026-07-07 — IRP reallocation out of 원리금보장 (3.9%)
- Decision: PENDING tax-branch check (W-9 ⇒ PFIC/FBAR advice first; W-8BEN ⇒ proceed).
  Target: qualified TDF up to 100%, or 70% index ETFs (unhedged) + 30% safe assets.
- Reasoning: longest-horizon capital earning lowest return; 3.9% vs ~6–8% expected over 25+ yrs.
- Expectation: IRP CAGR > 3.9% + 1.5pp over any rolling 5-year window.
- Judge on: first 5-year checkpoint 2031-07-01.
- Outcome: —

## 2026-07-08 — Experiment verdict: HAR volatility estimator vs default (mixed_vol_calc)
- Decision: NO production change. `har_vol_calc` stays on the shelf; no config wires it in.
- Evidence: HAR campaign `results/research_battery/20260708_194002_vol-har_vol_calc/`
  (5 variants, bootstrap 2000, walkforward 10y) paired cross-run against default-vol run
  `20260707_212812` via `analysis/research_harness/compare_runs.py` (same stationary-block
  machinery, common sample 13,422 days); table archived as
  `compare_vs_20260707_212812.csv` in the HAR run dir.
- Result: HAR is pointwise WORSE for every variant — Sharpe diff −0.042 (baseline),
  −0.032 (handcraft), −0.022 (shrinkage), −0.006 (hrp), −0.035 (equal); every 95% CI
  straddles zero; P(HAR beats default) only 0.13–0.40. Walk-forward (44 rolling 10y
  windows): mean window diff ≤ 0 for 4/5 variants, frac positive ≤ 0.57 — no regime
  where HAR reliably helps. Risk side decisively worse: baseline realized vol 37.0 vs
  32.9 pctpts (12% vol-target overshoot) and worst drawdown −248 vs −179 pctpts.
- Interpretation: the estimator is correctly built (causality bitwise-proven, 7/7 tests)
  but the hypothesis "multi-horizon blend improves daily-frequency sizing" is NOT
  supported here. The default `mixed_vol_calc` blends 30% of a 20-YEAR slow vol — that
  long anchor damps sizing swings; HAR's longest horizon (66d) is ~80× shorter, so all
  its components are fast, positions whip more, and realized vol overshoots target.
  HAR-RV's edge in the literature comes from intraday realized-vol inputs we don't have.
- Judge on: closed 2026-07-08 (pre-registered same-day judgment: point estimate + CI).
  Reopen only with (a) true intraday realized-vol inputs, or (b) a HAR variant that
  keeps a multi-year slow anchor as a fourth component.
- Outcome: the null (default estimator) wins again — third straight verdict where the
  boring incumbent survives a challenger. The battery is doing its job.
