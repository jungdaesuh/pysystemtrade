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

## 2026-07-09 — Experiment verdict: forecast-weight estimation (incl. HRP) vs fixed weights
- Decision: NO production change. Fixed forecast weights stay; `fw_*` variants remain
  research flags in the battery.
- Evidence: `results/research_battery/20260709_210216/` — baseline + fw_handcraft /
  fw_shrinkage / fw_hrp / fw_equal (new single-axis variants: forecast weights + FDM
  estimated, instrument weights fixed), bootstrap 2000, walkforward 10y, common
  13,422-day sample. Baseline anchor reproduced exactly (0.478 / 32.87 / 13,422),
  validating the battery extension itself.
- Result: full-period Sharpe diff vs fixed — fw_handcraft +0.031, fw_equal +0.027,
  fw_shrinkage −0.041, fw_hrp −0.039; every 95% CI straddles zero (and CIs are ~2×
  wider than on the instrument-weight axis); P(beats base) 0.32–0.62. Walk-forward
  (44 windows): NO variant wins even half (frac positive ≤ 0.43) and worst windows
  run −0.31 to −0.48 — full-sample edges are regime-concentrated, not robust. HRP
  specifically has nothing to cluster at 6 instruments × 4 rules.
- Side-findings (kept, not acted on): (1) estimated forecast weights + estimated FDM
  cut realized vol 32.9 → ~27.7 pctpts and worst drawdown −179 → −91..−109 pctpts at
  similar Sharpe — the estimated FDM is materially more conservative than the fixed
  one; if drawdown depth ever becomes the binding constraint, this axis is where the
  lever is. (2) The 2020s collapse that hit ALL estimated instrument-weight variants
  does NOT recur here (fw_equal 0.484 vs baseline 0.387 in the 2020s) — the collapse
  mechanism lives in instrument weighting specifically, not in estimation per se.
- Judge on: closed 2026-07-09. Reopen on the expanded universe (more instruments AND
  more rules give estimation something to work with).
- Outcome: the null wins a fourth straight time. Fixed weights remain undefeated at
  this breadth.

## 2026-07-10 — Paper rehearsal of Phase 1 deployment: PASS (`--live` path exercised)
- Decision: ran the supervised `--live` deploy_phase1.py rehearsal on PAPER account
  DUR207416 with $10,000 rehearsal capital, user-confirmed YES, during market hours,
  via the new fully-headless Gateway (IBC 3.24.1 + Xvfb, auto-login, port 4002).
- Result: 5/5 orders Filled in under a second — SGOV 68 @ $100.51, VTI 2 @ $372.41,
  VEA 14 @ $71.06, GLDM 9 @ $81.14, VGIT 11 @ $58.56; $9,948.76 deployed (98.5% of
  capital; remainder is whole-share rounding), commissions $1.00/leg exactly as the
  whatIf estimated, three fills price-improved vs their limits. The script's
  DECISIONS-block output rendered correctly.
- What this proves: the entire live order path (placeOrder → fill stream → commission
  reports → record block) works end-to-end. The real-money Phase 1 deploy now needs
  only: funded U-account + same command with real capital, supervised.
- Infrastructure note: Gateway now starts headless via `~/ibc/gatewaystart-headless.sh`
  (copy versioned at `scripts/ib/gatewaystart-headless.sh`); credentials in
  `~/ibc/config.ini` (mode 600, outside repo). No desktop, monitor, or manual login
  needed — this is also the September production mechanism.
- Outcome: PASS. Handoff next-action "supervised --live paper run" closed.

## 2026-07-10 — Data gap: FREE GAP-STITCH chosen (user decision)
- Decision: close the 2024-03→present price gap with `gap_stitch.py` — bootstrap the gap
  contract chains, IB historical fetches with includeExpired, repeated multiple-price
  roll-forwards. Pilot = the chapter-15 six. NO vendor subscription.
- Reasoning: funding plan is <$10k — far below the pre-registered ≥$50k vendor
  threshold. The cost rule decided this, exactly as designed.
- Expectation: continuous multiple/adjusted prices through the present for 6
  instruments; G1b bands hold (full-period Sharpe within ±0.10 of 0.478).
- Judge on: stitch completion (target before 2026-08-01; IB's ~2yr expiry window
  decays monthly — oldest gap contracts age out soonest, so sooner is materially better).

## 2026-07-10 — Gate 1 definition ADOPTED as written (user decision)
- Decision: `docs/custom/plans/gate1_parity_definition.md` adopted unchanged —
  G1a exact regression anchor (already passing), G1b data-transition bands,
  G1c sim↔production position parity; parity universe = chapter-15 six by declaration.
- Next: write the G1c comparison script and archive its first run.

## 2026-07-10 — Tax branch RESOLVED: W-9, resident alien (user answer)
- Consequence for the 2026-07-07 IRP entry: the W-9 branch fires → PFIC/FBAR exposure
  applies to Korean pooled funds. IRP reallocation into Korean TDFs/funds is ON HOLD
  pending professional tax advice (not a DIY determination). FBAR filing itself is
  likely already required if aggregate foreign accounts exceed $10k.
- XSP options: no longer blocked on branch-unknown (W-9 = standard US treatment incl.
  Section 1256 for index options), but remains out of policy scope until revisited.

## 2026-07-10 — Funding range: under $10k initially (user answer)
- Consequence: barbell fully viable at any size. Futures engine math is now binding:
  20% of <$10k is <$2k engine capital, BELOW one micro contract's ~$2-3k margin.
  Gate 3 (minimum-capital report) must formalize this — likely outcomes: raise engine
  allocation, add capital before go-live, or delay engine start while the barbell runs.
  Honest math, pre-registered here, to be run as Gate 3 when funding lands.
- Confirms the free-data path chosen above.

## 2026-07-10 — Gap stitch EXECUTED and G1b-certified: data current through today
- Decision: ran `scripts/data_utilities/gap_stitch.py --write` for the chapter-15 six.
  All six stitched 2024-03-28 → 2026-07-10 with zero skipped contracts; parquet backup
  at `~/pysystemtrade-backups/gap_stitch_20260710_215710/`.
- Method (validated in dry runs first): held chains from roll parameters; IB daily
  bars with includeExpired and endDateTime ANCHORED AT EXPIRY (the production fetcher
  anchors at now with 1y duration and can never reach the gap); price-scale validation
  against the seed's own last row (all six: factor 1, matches to the tick); rolls at
  desired_roll_date clipped to shared data; panama re-stitch; pre-gap daily returns
  verified bitwise-preserved per instrument.
- Known approximation (documented): MXP has a genuine 63-day IB data hole
  2025-03-17..2025-05-19 (CME FX symbology migration; the expired history lives only
  under the legacy MXP listing, discovered via dual-symbol probing). Bridged with flat
  returns + differential absorbed into the roll. Portfolio-level impact: none visible
  (max portfolio-curve gap after boundary: 3 days).
- G1b verdict (bands ADOPTED this morning): PASS — Sharpe 0.406 (anchor 0.478 ± 0.10),
  ann_std 34.59 (32.87 ± 15%), n_days 14,018 (> 13,422), backtest last date 2026-07-10.
  Checker: `analysis/research_harness/g1b_stitch_check.py` (rerunnable any time).
- Consequence: plan Phases 5-6 UNBLOCKED — contract chains now anchor on live
  contracts (CORN Z6, EUROSTX/US10/MXP U6, V2X V6, SOFR M9), so production sampling,
  daily price updates, and the Gate 2 paper reconcile streak can start.
- Judge on: G1b re-check after the first month of live daily updates (2026-08-10).

## 2026-07-10 — First daily production cycle PASS (pilot six) — Phase 5 complete
- Decision: brought up the daily price cycle on the stitched data via
  `scripts/data_utilities/daily_cycle_pilot.py` (production functions scoped to the
  six; the full-universe runner would spam errors on the ~94 unstitched instruments).
- Result: FX updated (EURUSD backfilled 3y first — 186-day overlap vs old data at
  ratio 1.00000); live contract chains SAMPLING (CORN 9, EUROSTX/MXP/US10 3 each,
  SOFR 15, V2X 6 contracts); per-contract price stores seeded (~250-500 daily rows
  each) through 2026-07-10; multiple+adjusted current at 2026-07-10 for all six.
- Known noise, triaged: (1) first-seed spike warnings are false positives (no prior
  history to compare against) — data wrote anyway except V2X/20260700, a dying
  contract (expires 2026-07-22) that is no longer price/forward/carry — no impact;
  (2) "can't get expiry" warnings for already-expired stitch-era contracts — inert;
  (3) EMAIL_CONTROL/email_store_filename unconfigured — cosmetic, no email alerting.
- Consequence: the sampling → prices → multiple/adjusted loop is OPERATIONAL. Gate 2
  (10 clean reconcile days) can start counting from the first automated run.
- Judge on: first automated Monday run (2026-07-13) — multiple/adjusted must advance
  to 2026-07-13 without manual help.

## 2026-07-11 — Items 1-3 executed: cron live, GATE 1 CLOSED, Phase 6 loop primed
- (1) CRON (user-approved): weekday 18:30 ET entry installed running
  `daily_cycle_pilot.py` (self-healing) with logging to `~/ibc/logs/daily_cycle.log`.
  First automated run: Monday 2026-07-13.
- (3) G1c PASS — `analysis/research_harness/g1c_parity_check.py`: sim and production
  paths produce BITWISE-identical final positions for all six (diff exactly 0.0).
  With G1a (anchor) and G1b (bands, 2026-07-10): **GATE 1 (parity) is CLOSED — PASS.**
- (2) Phase 6 bring-up (`scripts/data_utilities/phase6_bringup.py`, idempotent):
  total capital seeded from paper broker value ($1,000,171); strategy capital 100% to
  `paper_classic` (wiring added to private_config.yaml); production backtest ran
  (buffered optimal positions in Mongo, state pickled to
  ~/pysystemtrade-private/backtests); order generator produced 5 instrument orders,
  now on the stack: US10 −1, MXP −1, CORN −29, EUROSTX +4, V2X −58 (SOFR inside band,
  no order — correct). Rerun-dedup verified. Cosmetic: margin-allocation criticals
  (no margin tracking configured) — inert.
- Remaining untested link: `run_stack_handler` (contract orders → IB paper execution →
  fills). First live test Monday during market hours; a clean day = Gate 2 day 1 of 10.
- Judge on: Monday 2026-07-13 — automated cycle at 18:30 + supervised stack-handler
  session; positions must reconcile.
