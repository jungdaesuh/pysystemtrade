# Literature review: strategy & code upgrade candidates — 2026-07-18

Six parallel research units (trend signals / non-trend signals / portfolio
construction / vol sizing / execution / upstream delta), reconciled into one
ranked menu. Constraint honored throughout: four pre-registered nulls already
logged (HRP, estimated instrument weights, HAR vol, estimated forecast
weights) — candidates need published after-cost out-of-sample evidence, low
data burden, and a pre-registerable battery spec. Full unit reports lived in
session transcripts; this file is the synthesis of record.

## Tier 0 — correctness, adopted immediately (2026-07-18)

- **Upstream PR #1650 sign bug in SR-cost adjustment — CHERRY-PICKED.**
  `sysquant/returns.py:167` negated an already-negative cost SR, so the
  weight-ESTIMATION layer added costs to returns (rewarding expensive rules).
  Verified root cause locally (cost dict = SR of cost curves, negative by
  construction, `_get_annual_SR_for_returns_for_optimisation type="costs"`).
  Production runs fixed weights → positions unaffected (G1a anchor re-verified
  after adoption — see DECISIONS). CONSEQUENCE: the two estimation nulls
  (instrument weights, forecast weights) were computed on a tilted field —
  estimation picked weights against cost-REWARDED returns, then paid real
  costs in accounting. Both experiments deserve one correction re-run.
- We are otherwise **0 commits behind upstream** (fork point 883c8681,
  upstream now pst-group/pysystemtrade). Every IB/order-path fix of the last
  12 months is already in our fork.

## Tier 1 — cheap hygiene, no user decision needed (queue behind Gate 2p ops)

1. **statsmodels 0.14.0 → 0.14.6, then drop the scipy<1.15 cap and
   scipy==1.13.1 pin** (statsmodels #9584/#9542 fixed `_lazywhere` for
   scipy≥1.16). Verify anchor bitwise after. Our statsmodels surface is two
   call sites (reporting OLS, corr_nearest) — low risk.
2. **Schedule the existing cost-feedback reports** (`slippage_report.py`,
   `costs_report.py`) and update `spreadcosts.csv` when realized diverges
   >25%. Zero code. Wrong configured costs distort trade gating first-order
   at our account size.
3. **Execution measurement additions** (before any execution A/B): persist
   passive-vs-aggressive final state (now debug-log only,
   `algo_original_best.py:256-284`; `algo_comment` gets overwritten), a
   data-quality flag (live/delayed/sentinel) at submission, post-fill
   markouts (+1m/+30m mid), and rows for abandoned `missing_order` attempts
   (survivorship bias in TCA). CAVEAT logged: IB paper fills simulate no
   queue → paper A/Bs overstate passive quality; treat as relative only.
4. **ib_async 2.1.0 = latest; no action.** pymongo 3.11.3 is the oldest pin
   (EOL-risky, upstream-inherited) — watch, don't churn mid-gates.

## Tier 2 — pre-registered battery queue (PENDING USER approval of order)

Proposed order; each spec: paired stationary block bootstrap on daily returns
+ walk-forward n_eff≥4; one variant per slot; verdict logged win-or-null.

1. **Correction re-run of the two estimation nulls** (post-#1650 fix; same
   specs as originals). Expectation: still null (DeMiguel 2009, Carver's
   random-data study: weights barely matter at small N) — but integrity
   requires the re-test; direction of the bug was against estimation.
2. **Slow breakout ensemble** (Carver AFTS S21; breakout80+160 at ~10% each,
   carved pro-rata from EWMAC sleeve). After-cost crude SR ≈ 0.79 in Carver's
   own framework, cross-corr vs EWMAC 0.58 at matched speeds. Config-only
   (`systems/provided/rules/breakout.py` is native). H1: ΔSR ≥ 0 with lower
   drawdown dispersion; turnover delta ≈ 0.
3. **Speed pruning** — zero-weight fastest EWMAC variants on expensive
   instruments. The one direction our null streak actively supports (Man AHL:
   fast trend has materially lower net SR at retail costs; Quantica: ~63d
   lookback optimum). H1: SR non-inferior, costs strictly lower.
4. **Normalised momentum** (RAMOM, SSRN 2457647: ≥TSMOM with ~40% lower
   turnover; Carver normmom16/32/64 after-cost SR 0.75-0.82). Near
   config-only via rob_system rawdata. H1: SR non-inferior AND measured
   turnover down.
5. **Seasonally-adjusted carry** (AFTS S10 diagnostic: carry weakest exactly
   in seasonal asset classes; Macrosynergy 23-commodity panel). New rule =
   12m rolling mean of existing `raw_carry` — trivial, zero new data. H1:
   ΔSR>0 concentrated in CORN; carry turnover falls.
6. **Vol-blend ratio + buffer sweep** (Carver 2025-11: 25-36d EWMA
   near-optimal; blend is a shrinkage/turnover mechanism, unlike dead-end
   reactivity). `proportion_of_slow_vol` ∈ {0, 0.2, 0.3, 0.5} × buffer ×
   vol-span {25,35,50}. Bounded upside ≤~0.05 SR. NOTE: config already runs
   mixed_vol_calc with 0.3 slow — this validates, not innovates.
7. (After 1-6 clear) turning-point speed blending, TS basis-momentum, slow
   skew (V2X-concentrated), thresholded V2X vol-carry — all MED/LOW
   confidence, specs in unit reports.

## Tier 3 — structural, decided at go-live (Gate 3), not battery-first

- **Universe expansion 6→~15→~30 with cost/liquidity-gated selection is THE
  dominant lever**: Carver's published curve (net SR 0.69@N=1 → 1.75@N=28,
  handcrafted, cost-adjusted); expected +0.2-0.4 SR for us vs ≈0 from any
  weighting scheme at fixed N ("more instruments beats better weights by an
  order of magnitude"). Selection by cost/liquidity rules, never per-
  instrument backtest SR. Stepped fixed IDM per Carver lookup (cap 2.5) at
  pre-registered expansion dates.
- **Exogenous risk overlay** (`systems/risk_overlay.py`, native, off by
  default): vol-shock/corr-shock/leverage caps. Insurance, not alpha —
  acceptance = tail metrics improve with ΔSR ≥ −0.02 (low power expected and
  acceptable). This — not a dynamic IDM — is the correct correlation-regime
  response.
- **Dynamic optimization (AFTS S25)** for N≈100 under small capital: only
  after static expansion plateaus.
- **Execution**: keep original-best (validated by Carver's 12y live TCA:
  ~40-90% of spread cost saved vs market orders); candidates = adaptive-algo
  fallback on bad data, longer passive timeouts (300/600s hardcoded is
  impatient for daily-horizon urgency), V2X imbalance-trigger check
  (IMBALANCE_THRESHOLD=5 may misfire on thin books). A/B by order parity,
  ≥20-30 sessions, after the measurement additions land.

## Does-not-work (merged; do NOT spend battery slots)

Acceleration (Carver's own after-cost SR 0.06-0.18); GARCH/implied-vol/
regime/downside vol for sizing (RMSE-only literature; Carver 2025-11
explicit); Moreira-Muir vol overlays (Cederburg 2020 OOS failure, dies to
costs); tail-hedge puts (Man/AQR: negative EV vs trend's crisis alpha);
dynamic/estimated IDM (leverages up exactly when correlations are about to
spike); drawdown-triggered deleveraging beyond vol target (Kelly logic
already in target); fast mean reversion on daily data (AFTS S26 backtest
error acknowledged); 3y absolute value/mean-reversion (Carver 2025-03: SR
−0.48); COT (no causal value at our horizon; no EUREX coverage); calendar
seasonality (Bayesian p≈0.6 replication); cross-sectional anything at N=6
(one instrument per class); estimated weights at small N in ANY clothing
(DeMiguel; our nulls); trend-rule shape shopping beyond one diversifier
(Baltas-Kosowski: variants near-interchangeable); execution scheduling
algos/L2 data at 1-3 lot scale.

## Upstream-contribution candidates (user decides; good citizenship + review)

1. tif="DAY" fix → upstream issue #1580 is EXACTLY our 10349 failure mode,
   no PR exists. Our production evidence makes a strong PR.
2. Sentinel-quote normalization (no upstream equivalent found; note ib_async
   ≥2.0 "empty value" defaults as an alternative implementation upstream may
   prefer).
3. pyproject statsmodels bump (upstream's uncapped scipy breaks fresh
   installs on scipy≥1.16).
