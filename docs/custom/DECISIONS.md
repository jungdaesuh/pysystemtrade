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

## 2026-07-12 — External audit VALIDATED: Gate 1 REOPENED; remediation items 1-3 done
- Decision: an external review challenged the program's state; every checkable claim
  was verified empirically and CONFIRMED. Gate 1 is REOPENED and Gate 2's day count
  is DEFERRED until the audit's required sequence completes. Adopted in full.
- Confirmed findings: (1) G1b as adopted (no >5bd gaps) is violated by MXP's 44-bd
  hole; the checker tested portfolio-calendar only, ignored max_gap in its PASS, and
  didn't exit nonzero. (2) G1c compared two near-identical constructions, not stored
  production positions — too weak to close a gate. (3) Strategy/policy mismatch:
  policy says micro futures at 25% vol; implementation is standard contracts at 20%
  — the $1M paper run validates PROCESS, not the sub-$10k live strategy. (4)
  process_configuration_methods was in private_config.yaml but scheduling reads
  private_control_config.yaml → standard runners saw NO strategies. (5)
  statsmodels/scipy drift broke reconcile + Gate 3 report imports. (6) No trade/
  position limits configured. (7) zsh lacked PYSYS_PRIVATE_CONFIG_DIR (and the
  .bashrc export was mangled onto another line). (8) 4 custom files unformatted.
- Fixed tonight, with evidence: scipy pinned 1.13.1 (statsmodels imports OK;
  pyproject bounded scipy<1.15; requirements-lock.txt committed, 45 pins) and the
  G1a anchor re-verified BITWISE after the downgrade (0.478/32.87/13,422, run
  20260712_140940). private_control_config.yaml created; live check now returns
  run_systems -> ['paper_classic'], run_strategy_order_generator -> ['paper_classic'];
  misplaced block removed from private_config.yaml. ~/.zshrc export added, ~/.bashrc
  line unmangled. Black applied to all custom scripts (clean).
- REMAINING before Paper Day 1 counts: (a) amend G1b via decision entry (explicit
  pre-registered hole-bridge exemptions; per-instrument gap check; nonzero exit) and
  re-implement the checker faithfully; (b) strengthen G1c to compare STORED production
  optimal positions vs sim at recorded capital; (c) configure paper trade/position
  limits + alerts; (d) then the supervised stack-handler run and clean reconcile.
- REMAINING before live futures (unchanged by tonight): micro-futures strategy config
  at 25% vol per policy; Gate 3 on real funding; automated kill controls; separate
  live host; ten representative clean paper days.
- Lesson (for learnings/): closing a gate requires implementing the ADOPTED criterion,
  not a criterion that happens to pass — and config placement must be verified by the
  CONSUMING code path, not by where writing it felt natural.

## 2026-07-12 — Audit remediation complete: GATE 1 RE-CLOSED under amended, faithful criteria
- Decision: G1b AMENDED (per-instrument continuity ≤5bd with pre-registered hole-bridge
  exemptions — exactly one: MXP 2025-03-17..2025-05-19, 44bd; portfolio-calendar
  checking abolished) and G1c STRENGTHENED (stored Mongo optimal-position bands vs
  independent recomputation at recorded capital). Both criteria written into
  gate1_parity_definition.md; both checkers exit nonzero on failure.
- Results: G1b PASS (all six instruments continuity-clean, MXP via exemption; bands
  sharpe 0.407 / ann_std 34.58 / n_days 14,018 all in band; exit 0). G1c PASS (stored
  bands == recomputed bands at recorded capital $1,000,170.58, ≤1e-3 and same rounding,
  all six; exit 0). With G1a (bitwise anchor, re-verified post-scipy-pin today):
  **GATE 1 RE-CLOSED — under criteria that can actually fail.**
- Risk controls configured (audit item 5, paper tier): per-instrument position caps and
  1-day trade caps at ~2x the current $1M optimal positions (CORN 65, EUROSTX 12,
  MXP 6, SOFR 12, US10 6, V2X 140), written to Mongo via
  `scripts/data_utilities/set_paper_limits.py` (idempotent, versioned). Email store
  configured. Automated kill controls + alerts remain on the before-LIVE list.
- Monday is now eligible to count as Gate 2 Day 1 IF the supervised stack-handler run
  and reconcile are clean.

## 2026-07-12 — Audit round 2 adopted: Monday = COMMISSIONING; Gate 2 split PROPOSED (PENDING USER)
- Decision: second external audit verdict adopted — "GO for tightly supervised Monday
  pipeline commissioning; NO-GO for calling it final Gate 2 Day 1." Fixes executed this
  session: (F4) the five pre-cap orders were CANCELLED and REGENERATED through the
  active position limits (identical quantities, now limit-gated at creation);
  (F7) lockfile regenerated reproducibly (editable path removed, restore command in
  header); (F8-partial) private_config.yaml + private_control_config.yaml chmod 600;
  (F2) G1b checker gaining boundary/coverage/freshness assertions + regression tests;
  (F3) G1c gaining independent recompute path + reference/order/config-identity
  comparisons; (F6-partial) daily cycle gaining overlap lock + authenticated broker
  check + freshness assertion (agents in flight; validated before commit).
- PROPOSED Gate 2 redefinition (PENDING USER — adopting changes go-live criteria):
  split into **Gate 2p (process)**: 10 clean days of the paper pipeline on the
  chapter-15 config — proves execution, reconciliation, ops; and **Gate 2s (strategy)**:
  ≥10 clean paper days on the ACTUAL go-live configuration (micro contracts, 25% vol,
  universe set by Gate 3 capital math) before any live order. Monday counts toward
  Gate 2p only if adopted AND clean. Without adoption, Monday is commissioning only.
- Honest disposition of the rest: (F5) real alerting needs an SMTP credential only the
  user can provide (e.g. Gmail app password) — USER ITEM; interim state: criticals go
  to logs + email.log, reviewed at each supervised session. (F6-remainder) backtest/
  order/stack/report scheduling stays deliberately MANUAL until 3 clean supervised
  days, then gets scheduled — pre-registered here. (F8) wildcard :4002 listener needs
  a sudo firewall rule — USER ITEM (commands in handoff); separate live host + Gate 3
  + Phase-1 live hardening remain before-live queue, unchanged.

## 2026-07-15 — COMMISSIONING RUN EXECUTED: pipeline proven, one root-cause fix, one gate discovered
- What ran: four supervised stack-handler passes during market hours (first-ever
  execution through this repo's order path). Final state: **EUROSTX +4 COMPLETE at
  avg 6297.25 (4 slices); V2X -5 of -62 partial at avg 19.97 (5 slices)** — nine real
  paper fills, every one booked correctly through broker -> contract -> instrument
  stacks with matching broker-side positions and NO position break at close.
- Root-cause fix (committed): IB error 10349 (blank tif + order preset) killed every
  broker order at submission — same quirk as deploy_phase1, now fixed at the source
  in `sysbrokers/IB/client/ib_orders_client.py` (explicit tif="DAY" on market/limit/
  stop orders). Proven by the nine fills that followed.
- Commissioning war stories (all resolved): a marketable EUROSTX limit FILLED at IB in
  the same second the 10349 message killed it system-side -> position break (broker +1,
  system 0); flattened broker-side, which created the REVERSE break (system +1, broker
  0) because fills had been booked after all -> reconciled through the system's own
  position tables (balancing adjustments), not the broker. Rule captured in learnings.
  The stray's 43-minute life banked EUR 30 by luck; booked as commissioning noise.
- DISCOVERED GATE: the 'best' execution algo sizes slices from market depth; CME/CBOT
  delayed data provides none ("market conditions -> size zero"), so US10/MXP/CORN/SOFR
  never spawn broker orders. EUREX delayed data works. **Paper trading beyond EUREX
  requires either (a) CME market-data subscriptions (~$/mo, the cost plan expected
  this at live anyway) or (b) a market-order algo override for paper.** USER DECISION.
- Verdict: commissioning PASSED for the pipeline itself (the audit's "GO for
  supervised commissioning" fulfilled). NOT a Gate 2 day (Gate 2p/2s still PENDING
  USER; CME instruments blocked). Positions held into tomorrow: EUROSTX +4, V2X -5,
  with the open V2X instrument order resuming at the next supervised session.

## 2026-07-16 — Visa compliance note (J-1): passive investing permitted; futures go-live gets a legal check
- Research finding (web sources, logged): passive personal investing (stocks/ETFs/
  bonds, own money) is broadly permitted for J-1 holders — not "employment". The gray
  zone is frequent, businesslike trading that resembles an occupation, which could be
  characterized as unauthorized employment. USCIS defines no bright line.
- Applied to this program: Phase 1 barbell (buy + band-rebalance a few times/yr) is
  unambiguously passive — GREEN. Paper trading involves no income — no issue. The
  live futures engine (slow trend-following, low turnover, fully automated, own
  money, income incidental to the scholar role) sits passive-side of the line but is
  not zero-gray — AMBER.
- Pre-registered mitigation: before the September live-futures go-live, one
  consultation with an immigration attorney (separate from the tax professional)
  confirming the automated low-turnover engine is consistent with J-1 status; also
  review sponsor/program documents for outside-activity clauses. Barbell deployment
  does NOT wait on this.

## 2026-07-17 — GATE 2 SPLIT ADOPTED (user: "adopt"): 2p/2s now binding; clock starts today
- USER DECISION: the 2026-07-12 proposal is adopted as written. **Gate 2p (process)**:
  10 clean days of the paper pipeline on the chapter-15 config. **Gate 2s (strategy)**:
  >=10 clean paper days on the actual go-live configuration (micro contracts, 25% vol
  target, universe set by Gate 3 capital math). BOTH must pass before any live order.
- Clock: counting starts 2026-07-17 (adoption date). The 2026-07-15 commissioning run
  met the bar but does NOT count retroactively, per the proposal's own terms.
- Clean-day criteria (operator interpretation, pre-registered now; user may veto):
  (1) daily data cycle exit 0, all six pilot instruments fresh within 3bd;
  (2) system backtest + order generation ran for paper_classic;
  (3) all spawned orders progressed through the stacks without manual surgery —
      partial fills carried over (e.g. V2X grinding) are clean;
  (4) zero unresolved position breaks at day close (system vs broker);
  (5) no manual data or position repairs.
- Counting rules (pre-registered): days are cumulative, not consecutive. A day that
  fails due to an EXTERNAL cause (exchange holiday, vendor outage, data-subscription
  pending) simply does not count. A day that fails due to a DEFECT IN OUR PIPELINE
  (anything needing a code fix in the order/data path) RESETS the 2p count to zero —
  the gate exists to prove the process, so a process defect restarts the proof.
- CME-data blockage ruling (the 07-15 discovered gate): while CME/CBOT data remains
  inactive, an otherwise-clean day counts toward 2p, BUT Gate 2p cannot CLOSE until
  at least 3 counted days include broker-order execution on CME/CBOT instruments —
  the US leg must be proven end-to-end, not just EUREX.
- Consequence: Gate 2s work (micro + 25%-vol config build) is gated on the funding
  amount (Gate 3 capital math) -> waits on the user's deposit decision. 2p and 2s
  days may overlap once the 2s config exists.

## 2026-07-17 — Day-1 attempt: 2 clean V2X fills, then a pipeline defect found, root-fixed same day; day does NOT count
- Session (10:39-10:55 ET, supervised): EOD stack hygiene (safe_stack_removal cleared
  the stale 07-15 orders, partial fills preserved), fresh backtest + order generation
  through limits (5 orders; EUROSTX correctly zero — held +4 sits inside its band),
  then the stack-handler pass. V2X filled -2 @ 20.30 (broker -7 == system -7, zero
  break). US instruments still size-zero (CME data inactive, probed 10:33: Error 354).
- DEFECT: five consecutive V2X broker orders rejected by IB — Error 201 "Message must
  contain field # 44" (FIX Price). DB evidence: all five stored limit_price=0.0 from
  offside_price=0.0 — the delayed EUREX feed published a ZERO BID (empty-book
  sentinel) and the tick validity gate only checked isnan, so 0.0 passed as a real
  quote. Two filled orders just before had genuine prices (20.35/20.40).
- ROOT FIX (committed, tested): (1) `sysbrokers/IB/ib_futures_contract_price_data.py`
  `quote_price_or_nan_if_sentinel` — bid/ask <= 0 normalised to nan at the IB ticker
  boundary, restoring every downstream isnan validity gate; (2) the aggressive
  re-peg path (`check_current_limit_price_at_inside_spread`) returns the no-change
  sentinel on a nan side price instead of proposing nan as the new limit.
  8 regression tests in `tests/test_execution_quote_validity.py` (17 pass with G1).
- GATE 2p RULING (per the adopted counting rules, same day): this is a DEFECT IN OUR
  PIPELINE requiring a code fix in the order path -> 2026-07-17 does NOT count and
  the count resets (0 -> 0; no prior days lost). Next Day-1 candidate: Monday
  2026-07-20, running the fixed code.
- Bookkeeping: the five rejected zero-fill broker orders remain on the stack for
  tonight's EOD cleanup (allow_zero_completions); positions after session:
  EUROSTX +4, V2X -7, NLV ~$997.6k paper.

## 2026-07-18 — LITERATURE REVIEW (6 parallel units): one upstream bug adopted, upgrade queue PROPOSED
- Six-unit orchestrated review (trend / non-trend / portfolio / vol-sizing /
  execution / upstream delta); synthesis of record:
  `docs/custom/plans/lit_review_upgrades_2026-07-18.md` (ranked tiers + merged
  does-not-work list with citations).
- TIER-0 ADOPTED SAME NIGHT: upstream PR #1650 (sign error in SR-cost
  adjustment, sysquant/returns.py) cherry-picked as b85befbb after independent
  local verification of the root cause (cost dict = SR of cost curves,
  negative; our line double-negated -> estimation layer ADDED costs to
  returns). Upstream's 4 regression tests pass. G1a anchor re-verified BITWISE
  after adoption (0.478/32.87/13422, results/research_battery/20260718_023309)
  -> production fixed-weights path provably unaffected.
- HONESTY CONSEQUENCE: the two estimation nulls (estimated instrument weights
  2026-07-08; estimated forecast weights 2026-07-11) were computed with the
  bugged code in the weight-fitting path — biased AGAINST estimation (weights
  fitted on cost-rewarded returns, then charged real costs). Correction re-run
  of both, same specs, proposed as battery slot 1. Expectation: still null
  (DeMiguel 2009; Carver random-data), but the record must be clean.
- KEY SYNTHESIS FINDINGS: (1) universe expansion dominates all weighting
  cleverness (~order of magnitude in expected ΔSR; Carver's published N-curve)
  — a Gate-3/go-live design lever, not a battery experiment; (2) vol-sizing
  research direction declared EXHAUSTED (config already runs the
  best-evidenced blended EWMA; HAR null matches literature); (3) execution:
  keep original-best (Carver 12y live TCA), add measurement before any A/B;
  paper fills simulate no queue -> paper execution A/Bs are relative-only;
  (4) we are 0 commits behind upstream after the cherry-pick; our tif +
  sentinel fixes are upstream-PR candidates (issue #1580 matches tif exactly).
- PENDING USER: Tier-2 battery queue order (slot 1 correction re-run, then
  slow breakout, speed pruning, normalised momentum, seasonal carry,
  vol-blend/buffer sweep); Tier-1 hygiene timing (statsmodels 0.14.6 +
  drop scipy pin); upstream PR contributions yes/no.

## 2026-07-18 — BATTERY QUEUE ADOPTED (user: "approve queue"); slot 1 correction re-run STARTED
- USER DECISION: Tier-2 queue adopted in proposed order: (1) correction re-run
  of both estimation experiments post-#1650; (2) slow breakout ensemble;
  (3) speed pruning; (4) normalised momentum; (5) seasonally-adjusted carry;
  (6) vol-blend/buffer sweep. One slot at a time, verdict logged win-or-null
  before the next; specs in docs/custom/plans/lit_review_upgrades_2026-07-18.md.
- Slot 1 PRE-REGISTRATION (started 2026-07-18 ~02:50 EDT, jobs=4): all eight
  original estimation variants (handcraft/shrinkage/hrp/equal x instrument,
  fw_ x forecast), identical specs to the 2026-07-08/07-11 originals, on
  post-fix code. Baseline for pairing: run 20260718_023309 (post-fix anchor,
  bitwise-identical to the pre-fix anchor). Hypotheses unchanged from the
  originals; expectation: still null (DeMiguel; Carver random-data). Any
  variant whose paired bootstrap now EXCLUDES zero in favour of estimation
  overturns the original null and gets a fresh DECISIONS verdict; otherwise
  the original nulls are RE-CERTIFIED on clean code.

## 2026-07-18 — SLOT-1 VERDICT: all eight estimation nulls RE-CERTIFIED on fixed code (with an honest asterisk)
- Run 20260718_171342 (8 variants, specs identical to originals, post-#1650
  code); paired vs post-fix anchor baseline 20260718_023309; statistics =
  harness bootstrap (2000 reps, 25d blocks) + 10y walk-forward. Table:
  results/research_battery/20260718_171342/variant_vs_baseline_postfix.csv.
- PRE-REGISTERED PRIMARY (bootstrap CI excludes zero): NOT met by any variant
  -> original nulls re-certified; production stays on fixed handcrafted
  weights. The record is now clean: nulls hold on correct code.
- HONEST ASTERISK (observed, not acted on): the bug's removal shifted results
  in the predicted direction — point diffs now mostly positive (hrp +0.075,
  equal +0.061, fw_handcraft +0.089; P(beat) 0.82-0.89) and the hrp/equal
  walk-forward CIs sit entirely positive ([0.021,0.161] / [0.034,0.118],
  86%/77% windows positive). Under the pre-registered criterion this is not a
  win, and criteria-shopping after results is forbidden. IF the user wants to
  pursue it later: requires a NEW pre-registration (stricter primary, e.g.
  both bootstrap AND walk-forward CIs exclude zero, longer blocks) as a fresh
  queue slot — logged here as optional candidate, no default action.

## 2026-07-18 — SLOT 2 PRE-REGISTERED AND STARTED: slow breakout ensemble; slot 3 declared VACUOUS
- Slot 2 spec (variant `breakout_ens`, run_battery): add breakout80 +
  breakout160 (natural scaling, no scalar) at 0.10 forecast weight each,
  carved pro-rata from the EWMAC sleeve (16_64/32_128/64_256 x0.6 ->
  0.126/0.048/0.126), carry untouched at 0.50; FDM left at baseline
  (conservative against the variant). Paired vs post-fix anchor baseline
  20260718_023309, harness bootstrap + 10y walk-forward.
- PRE-REGISTERED CRITERIA (before results): WIN/ADOPT = bootstrap CI95 of
  Sharpe diff excludes zero from below (lo > 0). NULL/KEEP-BASELINE =
  anything else, incl. positive-but-not-significant. Secondary (reported,
  non-deciding): drawdown, turnover delta.
- Slot 3 (speed pruning) declared VACUOUS: chapter-15 baseline forecast
  weights already exclude ewmac2_8/4_16/8_32 (weights only on 16_64/32_128/
  64_256/carry) — the pruning the literature supports is already our
  baseline. No run needed; queue advances to slot 4 (normalised momentum)
  after slot 2.

## 2026-07-18 — SLOT-2 VERDICT: breakout ensemble NULL by pre-registered criterion (near-miss, logged faithfully)
- Run 20260718_171745, paired vs anchor 20260718_023309: Sharpe diff +0.028,
  bootstrap CI95 [-0.001, +0.058], P(beat)=0.972; walk-forward 44 windows,
  93.2% positive, wf CI [+0.018, +0.047]. Table:
  results/research_battery/20260718_171745/breakout_vs_baseline.csv.
- PRE-REGISTERED BAR (set before results): WIN requires bootstrap CI95 lo > 0.
  lo = -0.001 -> **NULL; baseline keeps its weights.** This is the discipline
  working as designed: a 97% probability-of-beating does not clear a bar set
  at CI-excludes-zero, and moving the bar after seeing results is forbidden.
- Not seed-shopped, not re-specced. IF revisited: fresh pre-registration
  required (e.g. same spec judged on new out-of-sample data as it accrues, or
  a joint criterion declared in advance). Optional future slot only.
- Queue: slot 3 vacuous (already logged) -> slot 4 (normalised momentum) next.

## 2026-07-18 — SLOT 4 PRE-REGISTERED AND STARTED: normalised momentum substitution
- Spec (variant `normmom_sub`): normmom16/32/64 (ewmac_calc_vol on vol-
  normalised price; rob_system fixed scalars 4.117/2.759/1.871) SUBSTITUTED
  for ewmac16_64/32_128/64_256 at identical weights (0.21/0.08/0.21), carry
  0.50 unchanged. Harness extended to record gross curves so cost drag
  (gross - net) is measurable; baseline re-run in-battery for like-for-like
  gross (also re-validates the anchor through the modified harness).
- PRE-REGISTERED CRITERIA (before results): STRICT WIN = bootstrap CI95 lo of
  Sharpe diff > 0. ADOPT-AS-SUBSTITUTE = SR non-inferior (CI95 lo > -0.05)
  AND annualised cost drag reduced >= 20% vs baseline (the published claim is
  cost reduction at equal signal quality — Dudler et al ~40% turnover cut).
  Anything else = NULL, keep EWMAC.

## 2026-07-18 — SLOT-4 VERDICT: normalised momentum NULL — cost-reduction claim did not replicate
- Run 20260718_172032 (baseline re-run in-battery: anchor 0.478/32.87/13422
  BITWISE through the gross-curve harness change). normmom_sub: SR diff
  +0.027, CI95 [-0.010,+0.062], P(beat)=0.929 -> non-inferior (lo > -0.05,
  criterion leg PASSED) but NOT a strict win. Cost drag: baseline 0.650 vs
  normmom 0.680 pctpts/yr -> -4.6% (an INCREASE; required: >=20% reduction).
- VERDICT: NULL — the substitution's published rationale (Dudler et al ~40%
  turnover cut) failed to replicate on our six instruments; keep EWMAC.
  Table: results/research_battery/20260718_172032/normmom_verdict.csv.
- Queue: slot 5 (seasonally-adjusted carry) next.

## 2026-07-18 — SLOT 5 PRE-REGISTERED AND STARTED: seasonally-adjusted carry
- Spec (variant `carry_seasonal`): new rule = 256bd simple rolling mean of
  raw_carry (cancels the annual seasonal cycle; AFTS treatment; rule lives in
  analysis/research_harness/battery_rules.py until adopted), scalar 30 reused
  from plain carry (conservative), added at 0.125 carved from the carry
  sleeve (carry 0.50 -> 0.375), EWMAC weights untouched.
- PRE-REGISTERED CRITERIA (before results): WIN = bootstrap CI95 lo of Sharpe
  diff vs baseline > 0. Else NULL. Secondary (reported, non-deciding):
  effect concentration in CORN, cost drag delta. Paired vs run
  20260718_172032's baseline (bitwise-validated anchor with gross curves).

## 2026-07-18 — SLOT-5 VERDICT: seasonally-adjusted carry NULL (significantly negative)
- Run 20260718_172226 paired vs 20260718_172032 baseline: diff -0.019, CI95
  [-0.036, -0.003] (excludes zero on the NEGATIVE side), P(beat)=0.009,
  walk-forward 2.3% windows positive. Worse in all five decades.
- VERDICT: NULL and rejected with prejudice — the AFTS-style seasonal mean at
  our spec (256bd, scalar 30, 0.125 weight) HURT. Rule remains quarantined in
  battery_rules.py; carry keeps 0.50. Secondary (CORN concentration) moot at
  a negative portfolio-level result.
- Queue: slot 6 (vol-blend x span x buffer validation sweep) — final slot.

## 2026-07-18 — SLOT 6 PRE-REGISTERED AND STARTED: vol-blend x span x buffer validation sweep (final slot)
- Spec: 36 cells — vol span {25,35,50}bd x proportion_of_slow_vol
  {0,0.2,0.3,0.5} x buffer_size {0.05,0.10,0.15}; cell d35_s30_b10 must
  reproduce the baseline bitwise (sanity anchor). All other config unchanged.
- PRE-REGISTERED CRITERIA (before results): this is a VALIDATION sweep of the
  current defaults, per Carver 2025-11 (25-36d near-optimal; blend marginal).
  ADOPT-CHANGE only if a cell beats d35_s30_b10 with paired bootstrap CI95
  lo > 0 AND the improvement is monotone-plausible (neighbouring cells agree
  in direction, guarding against a lone lucky cell). Expected outcome:
  defaults re-certified, no change.

## 2026-07-18 — SLOT-6 VERDICT: defaults re-certified; BATTERY QUEUE COMPLETE
- Run 20260718_172433 (36 cells): sanity anchor vb_d35_s30_b10 reproduced the
  baseline BITWISE (0.478/32.87/13422). Best cell vb_d25_s50_b5: diff +0.024,
  CI95 [-0.010,+0.060], P(beat)=0.914 -> no cell clears CI lo > 0. VERDICT:
  NULL — vol span 35d / slow blend 0.3 / buffer 0.10 stay. Observed structure
  (reported, not acted on): coherent insignificant tilt toward MORE slow-vol
  blend (s50 tops every span) and TIGHTER buffer (b5 tops every group) —
  direction matches Carver 2025-11; magnitude never significant.
  Table: results/research_battery/20260718_172433/sweep_vs_anchor.csv.
- QUEUE COMPLETE (adopted 2026-07-18, executed same day): slot 1 = eight
  estimation nulls RE-CERTIFIED on post-#1650 code (asterisk logged); slot 2
  = breakout ensemble NULL by CI lo -0.001; slot 3 = VACUOUS (fast speeds
  already pruned in baseline); slot 4 = normmom NULL (cost claim failed to
  replicate, drag +4.6%); slot 5 = seasonal carry NULL, significantly
  negative; slot 6 = defaults re-certified.
- BOTTOM LINE: the chapter-15 baseline survived the full literature-driven
  assault — now including the corrected estimation code. The research
  factory's cumulative verdict stands: at N=6 with our costs, no signal,
  weighting, vol, or tuning upgrade clears a pre-registered bar. The one
  literature-backed lever with large expected effect remains UNIVERSE
  EXPANSION (+0.2-0.4 SR for 6->30), which is a Gate-3/funding decision, not
  a battery experiment. Tier-1 hygiene (statsmodels 0.14.6 + drop scipy pin;
  scheduling cost reports; execution measurement fields) remains open as
  ops work, no user decision required beyond timing.

## 2026-07-20 — EUROSTX spike quarantine root-caused; operator approval executed (designed workflow)
- Root cause of the 07-17..07-20 EUROSTX Sep26 PRICE gap: the contract's
  stored HOURLY series was EMPTY (never populated), so every price-update
  cycle false-positived the spike check and ABORTED the contract's writes —
  chronic, silent (spike email unsent: no SMTP credential, known user item).
  Direct IB fetches verified the "spike" was a normal -0.2%/day move.
- Intervention (2026-07-20 ~19:20, logged): mirrored the interactive manual-
  check approval — fetched cleaned broker prices, wrote hourly (437 rows) +
  daily with check_for_spike=False, merged, propagated multiple+adjusted.
  EUROSTX now current intraday. This is pysystemtrade's DESIGNED operator
  workflow (interactive_manual_check_historical_prices equivalent), not a
  code change. Script: scratchpad/approve_eurostx_spike.py (session copy).
- Residual noise (left alone deliberately): V2X 2026-07/08/09 bare contracts
  flag the same empty-series false positive; none is in the V2X trio, no
  downstream effect. If they persist, same approval applies.
- Ops note: Gateway dropped once ~19:15 (unscheduled; relaunched in 10s,
  no impact). Watch for recurrence.
- GATE 2p DAY-1 JUDGMENT: PENDING USER — criteria 1-4 met (cycle exit 0 and
  fresh; backtest+orders ran; stack flow clean, 1 V2X fill @20.00, zero
  break). Criterion 5 ("no manual data repairs") requires a ruling: the
  spike APPROVAL is the system's designed human-in-the-loop gate (operator
  duty, prices verified, nothing repaired retroactively; condition predates
  the 2p clock) — reading A counts the day; strict reading B does not.
  Recommendation: A. User adjudicates.

## 2026-07-20 — USER RULING: Day 1 COUNTS — Gate 2p at 1/10
- User adopted reading A: designed human-in-the-loop gates (price-spike
  approval with verification, roll confirmations and the like) are normal
  operatorship and do NOT void a clean day. Precedent recorded for future
  judgments. Criteria 1-4 were met outright; criterion 5 satisfied under
  this ruling.
- GATE 2p: 1/10 clean days. Constraint unchanged: >=3 counted days must
  include CME/CBOT execution before 2p can close — data activation (user
  portal/deposit) remains the critical path.

## 2026-07-21 — Evening ops: V2X bare-contract quarantines approved (same empty-series pattern)
- Verified before writing: stored == broker where both existed (Aug 18.35,
  Sep 19.15 identical); July stored EMPTY vs broker 17.75 — a sane contango
  curve point. Approved all three via the designed check_for_spike=False
  write (July +369h/+164d rows, Aug +372h, Sep +317h). Precedent per the
  2026-07-20 user ruling: designed operator gates, day-neutral.
- No session ran today (scheduling gap, owned in chat; standing weekday
  09:37 schedule created with user approval) -> Gate 2p remains 1/10,
  nothing to judge. Cycle clean; EUROSTX spike fix HELD (no recurrence);
  CME data dark day 6.

## 2026-07-23 — Day-3 session: two background KILLS (clean), root-caused, completed via foreground re-run
- Two consecutive scheduled sessions (Day-2 07-22, Day-3 07-23) launched with
  run_in_background were KILLED early at the spawn step. Investigated (not
  assumed): kernel log shows NO OOM today (last OOM 07-16); 53Gi RAM free; IB
  healthy. Each kill left a verifiably SAFE state — instrument+contract orders
  spawned with zero fills, broker stack empty, zero dangling IB orders,
  broker positions == system positions. No pipeline defect (no code bug) ->
  not a day-voiding event under the 2026-07-17 rules; it's an incomplete run.
- Root cause: launch method. Day-1 (WORKED) was foreground, auto-moved to
  background on the 600s timeout. Direct-background launches get reaped.
  Fix adopted: launch these sessions foreground with a timeout (learnings
  2026-07-23). Standing-session cron prompt should follow suit.
- Day-3 re-run (foreground, 8 min, auto-backgrounded, exit 0): V2X filled
  -1 @ 20.40 -> position -9; EUROSTX +4 unchanged; broker == system (-9/+4),
  zero break, zero rejection. One filled broker order rests for evening
  cleanup. Clean execution.
- GATE 2p Day-3 JUDGMENT: PENDING USER after the evening cycle. Criteria 1-4
  met (data sanity clean; backtest+orders through limits; clean fill; zero
  break). The two upstream kills were operational interruptions with verified
  clean state, not pipeline defects — recommendation: COUNTS (would bring
  Gate 2p to 2/10, pending user; Day-2 07-22 was never completed and does
  not count).

## 2026-07-24 — Day-4 session: kill root cause is MACHINE MEMORY CONTENTION (user's fusion job), not launch method
- Day-4 (foreground, auto-backgrounded) was KILLED — breaking the 2026-07-23
  "foreground survives" theory. Re-investigated properly: NOT a code/pipeline
  defect. Root cause = host memory pressure: 1.3Gi free RAM, swap 50/54Gi
  (93%). Top consumer = PID 2613902, a 15.5Gi simsopt stellarator
  optimization (single_stage_banana, user's ACTIVE fusion research, started
  08:13, git worktree) — NOT touched (user's work). Trading sessions that run
  long as backgrounded tasks get squeezed out under this load. journalctl
  showed no OOM line for the python session specifically, but the pressure is
  real and sufficient.
- SAFETY through both kills: verified clean each time. The first (killed)
  session even FILLED V2X -1 (->-10) and BOOKED it correctly before dying —
  system == broker at -10, zero break. This is why the post-kill
  IB-vs-system check is mandatory (a killed session can hide a booked fill).
- Completion: short 3-min foreground re-run (completes without backgrounding,
  minimal reap window) filled another V2X -1 -> position -11; system ==
  broker (-11 / EUROSTX +4), zero break, zero rejection. Day-4 execution
  CLEAN.
- REVISED understanding (supersedes 2026-07-23 launch-method theory): kills
  are load-dependent, not deterministic by launch path. Mitigation: keep
  sessions SHORT (--minutes 3) so they finish in-foreground; the day's
  pipeline-proof is achieved as soon as one fill books cleanly. Standing cron
  updated to --minutes 3. Persistent memory tightness on this shared host is
  a USER-AWARENESS item (fusion jobs + multiple sessions + firefox).
- GATE 2p Day-4 JUDGMENT: PENDING USER. Criteria met (data clean; orders
  through limits; two clean V2X fills; zero break; the interruptions needed
  verification but NO manual repair). Recommend COUNTS.

## 2026-07-25 — Ops tooling moved into the repo after /tmp sweep; missed Friday cleanup completed
- FRAGILITY FOUND: the nightly ops scripts lived only in the session scratchpad
  (/tmp) and were swept. Every scheduled pass referencing them would have
  failed; Friday 07-24's evening cleanup did not run (stacks still held 5
  instrument / 5 contract / 2 filled V2X broker orders on Saturday morning).
- FIXED: promoted to version-controlled scripts —
  scripts/data_utilities/eod_stack_cleanup.py, probe_market_data.py,
  approve_contract_spike.py, plus stack_reporting.py (shared print_stacks, now
  also used by commission_stack_handler.py — duplicate removed, SSOT).
  probe_market_data.py resolves contracts via the system's own priced-contract
  mapping instead of hardcoded conIds, so it survives rolls. All scheduled jobs
  repointed at the repo paths.
- Cleanup completed Saturday: all three stacks cleared (Friday's two V2X fills
  were already booked). Positions verified: system == broker (V2X -11,
  EUROSTX +4), zero break. NLV 1,000,631.
- Probe caveat recorded: run during trading hours only — Saturday's run showed
  NO LIVE DATA for all six including EUREX instruments, which reflects closed
  markets, not the subscription. CME/CBOT activation therefore UNCHANGED at
  last known state (dark since 07-16); next real check is Monday's session.
- GATE 2p: unchanged, 1/10 counted. Day-3 (07-23) and Day-4 (07-24) executed
  clean and remain PENDING USER judgment (recommend both COUNT -> 3/10).

## 2026-07-27 — CME/CBOT data ACTIVE; trading-hours timezone-frame defect found + fixed; Gateway killed by LAN IP flap; stacks cleaned flat
- CME/CBOT DATA ACTIVATED (9-session drought over): probe returned LIVE
  bid/ask with depth for all six — CORN 474.5x152/474.75x208, US10, MXP,
  SOFR, EUROSTX, V2X. The four US instruments are unblocked; Gate 2p's
  ">=3 counted days with CME/CBOT execution" is now reachable.
- SPIKE APPROVALS (verified first, stored==broker at every overlap):
  EUROSTX/20260900 (Friday +1.3% recovery 6219->6301, live 6358 consistent;
  +34 hourly +1 daily rows), CORN/20260900 and /20261200 (moves ~2%,
  continuous into Monday's live quotes; +8 hourly +1 daily each). Merged
  prices rewritten. Non-trio CORN 2027xx flags left per standing rule.
- PASS 1 (10:10-10:18): V2X filled 3 x -1 @ 20.05 -> position -14, booked
  broker->contract->instrument, zero break. US four spawned contract orders
  but produced NO broker orders.
- DEFECT FOUND (config, not code): saved trading-hours windows in
  sysbrokers/IB/ib_config_trading_hours.yaml are authored in LONDON host
  time, and GMT_offset_hours defaulted to 0, but okay_to_trade_now()
  compares against the HOST clock (EDT) — every window sat 5h late. US
  markets "opened" 15:00 EDT; CORN (day session ends 14:20 EDT) could NEVER
  trade; today's V2X fills slipped through the mis-shifted EUREX window.
  FIX (both knobs the framework provides, in the private dir):
  private_config_trading_hours.yaml authored in EDT frame (US/Central
  10:00-15:00, MET 03:00-10:00, etc.) + GMT_offset_hours: -4 in
  private_config.yaml. VERIFIED: US10/MXP/SOFR okay_to_trade=True in the
  liquid window, CORN correctly gated to its real 11:30-14:20 EDT
  intersection, EUREX correctly closed after 10:00 EDT. NOTE: set
  GMT_offset_hours to -5 at the November DST change.
- RE-RUN (permitted once, validating the fix): US10 broker order 31
  (-1 limit @ 108.484375) submitted to IB and managed by 'best' — then the
  Gateway DIED mid-manage (ConnectionError: Socket disconnect).
- GATEWAY DEATH ROOT CAUSE: journal shows the host LAN IP flapping
  192.168.68.52 <-> .53 at exactly 10:27 (tailscaled "gateway and self IP
  changed" x5, 10:27-10:28). Network bounce, NOT memory (75Gi available),
  NOT a pipeline defect. USER ITEM: host has a DHCP lease fight or dual
  interfaces racing; static IP / single interface would stop random IB
  session kills.
- POST-INTERRUPTION RECONCILIATION (mandatory, 07-24 precedent): US10 order
  found RESTING UNFILLED at IB (no hidden fill); positions matched exactly
  (V2X -14, EUROSTX +4). safe_stack_removal cancelled it and cleared all
  three stacks; IB confirms ZN order status=Cancelled filled=0. Final state
  flat and reconciled; no trading after the cleanup (re-run allowance
  spent, Gateway trust low).
- GATE 2p Day judgment: PENDING USER (do not self-judge). Facts for the
  ruling: 3 clean V2X fills booked with zero break; a CONFIG defect was
  found and fixed mid-session (the 07-17 voiding rule names code fixes);
  no CME/CBOT fill today (US10 cancelled unfilled). Also still pending:
  Days 3-4 rulings (recommend both COUNT -> 3/10).

## 2026-07-28 — FIRST CME/CBOT EXECUTION: US10, MXP filled complete; SOFR partial; zero break
- Probe: all six LIVE (second consecutive session — activation stable).
- Data sanity clean: EUROSTX multiple tail 6333.0 @ 07-27 16:00; no trio
  spikes (far-CORN 2027xx noise only).
- Backtest orders: US10 -2, MXP -2, CORN -21, SOFR -5, V2X -44.
- Handler pass (10:13-10:17, corrected trading-hours config active):
  US10 -2 FILLED @ 108.734375 (both lots at the offer — passive, zero
  spread cost); MXP -2 FILLED @ ~0.05707; SOFR -2 of -5 @ 96.005/96.00;
  CORN untouched (real-hours window opens 11:30 EDT — correct gating);
  V2X skipped (EUREX window closed 10:00 EDT — correct gating). US10 and
  MXP orders completed and cleared off all stacks in-session.
- Reconciliation: ZERO breaks across all five positions (V2X -14,
  EUROSTX +4, US10 -2, MXP -2, SOFR -2); no working orders at IB.
  Remaining stack orders (CORN -21, SOFR -3 residual, V2X -44) carry to
  evening cleanup; tomorrow regenerates.
- Yesterday's trading-hours frame fix is thereby VALIDATED in production:
  the US four were blocked solely by the config defect, now proven fixed
  end-to-end with real fills.
- GATE 2p Day judgment: PENDING USER. Facts: fully clean session, no
  defects, no interruptions, first day satisfying the "CME/CBOT
  execution" criterion. Pending alongside: Days 3-4 (07-23/24, recommend
  count) and Day-5 (07-27, config-defect ruling).

## 2026-07-28 — USER RULING (binding): no borrowing, no margin loans
- The user rules: NO margin loans, NO borrowing of any kind, ever. Dropped
  "margin application" from the pending list.
- Clarification recorded for precision: futures performance-bond margin is
  collateral posted from own cash, not borrowing — the program's futures
  trading remains permitted and remains fully cash-collateralized with the
  conservative go-live config (micro contracts, 25% vol target). If broker
  account-type taxonomy ever requires a "margin-type" classification for
  futures permissions, surface to the user BEFORE proceeding; in no case is
  cash ever borrowed.

## 2026-07-29 — Day-7: clean session, SOFR fill, zero break
- All six LIVE (third consecutive session). Data sane, no trio spikes.
- Orders: CORN -21, SOFR -3, V2X -45 (US10/MXP inside buffers — no orders,
  buffering working as designed).
- Fill: SOFR -1 @ 95.98 -> position -3. CORN gated to 11:30 window, V2X
  gated by EUREX close — both correct.
- ZERO breaks (V2X -14, EUROSTX +4, US10 -2, MXP -2, SOFR -3); no working
  orders at IB; no interruptions. Second consecutive CME-execution day.
- Day judgment PENDING USER (now five days pending: 3, 4, 5, 6, 7).

## 2026-07-29 evening — V2X trio quarantine (real vol spike) verified + approved; multiples healed; clean close
- Cycle succeeded but tonight's V2X trio (20260900c/20261000p/20261100f, HELD
  -14) was spike-quarantined: V2X rallied ~+3.3% intraday (19.95 -> 20.6) as
  EUROSTX fell — genuine vol move. VERIFIED stored==broker at every daily
  overlap; morning live probe (20.2/20.25 @ 10:07) independently confirms.
  Approved all three; +16/+13/+11 hourly rows; re-ran multiple/adjusted
  update (cycle had run against quarantined data) — V2X multiples now
  current to 07-29 15:00 @ 20.6.
- SOFR flags (2026-27 months) non-trio (trio is 2029) — noise. CORN 2027xx
  noise unchanged.
- Cleanup verified: stacks 0/0/0. ZERO breaks; positions V2X -14,
  EUROSTX +4, US10 -2, MXP -2, SOFR -3. NLV 999,583 (-$3.5k on the day:
  short vol into a vol rally + long equity into a dip — position P&L, not
  operational).

## 2026-07-30 — Day-8: clean session, SOFR complete at optimal, zero break
- All six LIVE (fourth consecutive). Data sane; no trio spikes overnight.
- Fill: SOFR -2 @ 95.965 -> position -5 (optimal band reached; order
  completed in-session). CORN/V2X untouched — session-timing gap (pass at
  ~10:14 misses EUREX close 10:00 and CORN open 11:30), fix options put to
  user 07-29, awaiting choice.
- ZERO breaks (V2X -14, EUROSTX +4, US10 -2, MXP -2, SOFR -5); no working
  orders; no interruptions. Third consecutive CME-execution day.
- Days pending user ruling: 3, 4, 5, 6, 7, 8.

## 2026-07-30 — CORRECTION: gateway kills are NetworkManager connectivity probes, NOT DHCP
- SUPERSEDES the 07-27 entry's root cause ("DHCP lease fight or dual
  interfaces racing"). That was inferred from a DHCP-renewal line 49s before
  the flip and was WRONG — an over-read of a coincidence.
- ACTUAL MECHANISM (journal 07-30 10:29:18): NetworkManager's periodic
  connectivity probe (http://connectivity-check.ubuntu.com/, configured in
  /usr/lib/NetworkManager/conf.d/20-connectivity-ubuntu.conf) momentarily
  fails; NM drops to CONNECTED_LOCAL, executes "policy: set 'PlasmaLab'
  (wlp174s0) as default for IPv4 routing and DNS", then reverts to
  enp173s0 ~1s later. Default route + DNS move twice per event.
- FREQUENCY: ~18 flips/day, ~130 in the last 7 days (Jul 23-30). Each is a
  chance to sever a live IB socket; two Gateway deaths so far (07-27
  mid-trade, 07-30 post-session).
- HOST HAS BOTH LINKS BY DESIGN (user wants Wi-Fi as fallback): enp173s0
  192.168.68.52 metric 100, wlp174s0 192.168.68.53 metric 600, same Deco
  router 192.168.68.1/22, lease 7200s.
- PRESCRIBED FIX (user's sudo): drop
  /etc/NetworkManager/conf.d/99-connectivity-off.conf with
  [connectivity]\nenabled=false, reload NetworkManager. Preserves genuine
  carrier-loss failover to Wi-Fi (link-state driven), removes probe-driven
  false alarms. Static IP / Deco address reservation NO LONGER NEEDED —
  withdraw that recommendation.
- PROCESS NOTE: the first root cause was published to the user before the
  surrounding journal lines were read. Read the full event window before
  naming a cause.

## 2026-07-30 evening — clean close, NLV recovers +$7.3k
- Cycle succeeded; Gateway self-healed after the 10:29 probe-flip death.
  Prices current to 07-30 for all instruments.
- Spike flags all NON-TRIO (V2X/20260800 vs trio 0900/1000/1100; SOFR
  2026-27 vs trio 2029; CORN far months) — noise, no approvals needed.
- Cleanup verified: stacks 0/0/0. CORN -20 and V2X -43 zero-fill completed
  (session-timing gap, unchanged pending user's schedule choice).
- ZERO breaks; positions V2X -14, EUROSTX +4, US10 -2, MXP -2, SOFR -5.
- NLV 1,006,839 (+$7,256 on the day, +$3.7k week-to-date): vol fell back
  (short V2X gained) while EUROSTX rallied 6252->6356 (long +4 gained) —
  both legs worked. Yesterday's -$3.5k more than recovered.
- Route flips continue (~10 since noon) — the connectivity-probe fix is
  prescribed but NOT yet applied (needs user sudo).

## 2026-07-31 — Day-9: clean session, SOFR fill; crons renewed
- All six LIVE (fifth consecutive). Data sane; no trio spikes overnight.
- Risk-off session at the open: CORN 473.75->464.75 (-1.9%), US10 108.5->
  108.08, SOFR 95.955->95.89. Backtest deepened shorts accordingly.
- Fill: SOFR -1 @ 95.89 -> position -6. CORN -21 and V2X -47 zero-filled
  again (session-timing gap, unchanged pending user's schedule choice).
- ZERO breaks (V2X -14, EUROSTX +4, US10 -2, MXP -2, SOFR -6); no working
  orders; no interruptions. Fourth consecutive CME-execution day.
- CRONS RENEWED before the 08-01 expiry: morning 3260f938 (09:37 wkdy),
  evening 3184ceee (18:47 wkdy); old cc9dca64/2e11985b deleted. Both now
  carry the known-context section (session-timing gap, NM route flips) so a
  fresh session does not re-diagnose settled issues. NOTE: session-only,
  7-day expiry -> renew again by 2026-08-07.
- Days pending user ruling: 3, 4, 5, 6, 7, 8, 9.

## 2026-07-31 evening — clean close; recurring spike noise investigated and cleared
- Cycle succeeded; prices current to 07-31. Cleanup verified, stacks 0/0/0.
- ZERO breaks; V2X -14, EUROSTX +4, US10 -2, MXP -2, SOFR -6.
- NLV 1,008,174 (+$1,335 on the day; +$7,543 on the week from 1,000,631).
- RECURRING SPIKE NOISE INVESTIGATED (the same 9 flags nightly: CORN
  20270300/0500/0700, SOFR 2026-27 months, V2X 20260800). NOT the 07-20
  empty-series quarantine failure mode: these contracts hold 439-586 stored
  rows and their daily series are COMPLETE with no gaps 07-22..07-30. The
  flags come from jumpy hourly bars on illiquid far months; the daily write
  lands regardless, so the merged series stays intact. VERDICT: cosmetic,
  no data loss, no action needed. Do not re-investigate.
- RESIDUAL RISK NOTED: 9 nightly false flags is alert fatigue — a real trio
  flag could hide among them. Mitigated today by filtering flags against the
  trio list programmatically (now baked into both cron prompts). If the
  noise grows, consider a per-contract spike threshold for far months.

## 2026-08-02 — USER APPROVED Option 1: morning session moved to 08:57, midday CORN pass added
- Fixes the session-timing gap (pass at ~10:14 landed between EUREX close
  10:00 and CORN open 11:30; V2X frozen at -14 vs optimal ~-61, CORN never
  traded).
- New schedule (all weekdays): 08:57 morning session 91314987 (trading pass
  lands ~09:30-09:45, inside EUREX window; morning pass no longer cleans
  stacks — leftovers carry to midday); 11:36 midday light pass 85663c3b
  (executes stack leftovers in CORN's 11:30-14:20 window; no backtest, no
  approvals); 18:47 evening ops 3184ceee unchanged. Old morning 3260f938
  deleted.
- Expected from tomorrow: V2X/EUROSTX execute in the morning, CORN gets its
  first fill at midday. All session-only crons; renew by 2026-08-07/09.

## 2026-08-03 — Day-10 MORNING pass: Option 1 schedule VALIDATED — V2X trades again
- First session on the 08:57 schedule; handler pass ran 09:28-09:32, well
  inside the EUREX window. All six LIVE; data sane; no trio spikes.
- Fill: V2X 3 x -1 @ 19.45 (1 limit + 2 market — algo escalation working)
  -> position -17, converging toward optimal ~-62. First V2X execution
  since 07-27; the timing gap is closed.
- US10/MXP/SOFR inside buffers — no orders (correct). CORN -21 on stack
  awaiting the 11:36 midday pass (first-ever CORN fill expected).
- ZERO breaks; no working orders; stacks intentionally left up for midday
  per the new protocol.

## 2026-08-03 — Day-10 MIDDAY pass: CORN'S FIRST FILLS — all six instruments now execute
- First midday pass (12:06-12:15). Gateway had died again since morning
  (route-flip issue, fix still awaiting user sudo) — relaunched cleanly.
- OPERATOR ERROR, harmless but logged: first handler invocation had a typo
  ($HOOME) so private config didn't load and the connection tried default
  port 4001 (nothing listens there) and failed cleanly. No orders, no side
  effects. Re-ran correctly. Lesson: the private-config fallback silently
  targets DEFAULT ports — a wrapper script exporting the env var would
  remove this class of error.
- CORN FIRST FILLS: 2 x -1 @ 469.75 / 470.00 -> position -2. With this,
  ALL SIX instruments have executed through the full pipeline. Remaining
  CORN -19 carries (limit-clipped grind, as designed).
- ZERO breaks across all six positions (V2X -17, EUROSTX +4, US10 -2,
  CORN -2, MXP -2, SOFR -6); no working orders.
- Option 1 schedule fully validated: EUREX morning + CORN midday both
  delivered on day one.

## 2026-08-03 evening — clean close on the first Option-1 day
- Cycle succeeded; prices current to 08-03. Only the known 9 far-month
  noise flags (investigated 07-31, cosmetic).
- Cleanup verified: stacks 0/0/0. CORN -19 and V2X -45 remainders zero-fill
  completed as designed; tomorrow regenerates at fresh prices.
- ZERO breaks across all six held instruments (V2X -17, EUROSTX +4,
  US10 -2, CORN -2, MXP -2, SOFR -6).
- NLV 1,008,421 (+$247 on the day). Long EUROSTX and short V2X both gained
  on the equity rally / vol decline; rate shorts gave some back.
- Day-10 was the first fully-covered day: EUREX executed in the morning
  pass, CORN at midday, all six instruments now proven through the
  pipeline. Days pending user ruling: 3,4,5,6,7,8,9,10.
