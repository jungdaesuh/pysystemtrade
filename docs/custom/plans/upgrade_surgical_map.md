# Surgical Upgrade Map — pysystemtrade fork

**Status:** Draft
**Last updated:** 2026-07-07

Precise incision points for upgrades, each anchored to current code and to 2025–2026
literature. Every item is gauntlet-gated: it earns weight only by surviving
`analysis/research_harness/run_battery.py` extended with walk-forward + bootstrap
(see `docs/custom/plans/portfolio_policy.md` gates). Ordered by expected value per effort.

## 1. HAR volatility estimator — drop-in, zero surgery

- **Where:** `sysquant/estimators/vol.py` — add `har_vol_calc()` beside `mixed_vol_calc`
  (line ~120). The config hook already exists: `volatility_calculation.func` is
  string-resolved (rob_system config points at `sysquant.estimators.vol.mixed_vol_calc`),
  so a new function is a pure addition — no core edits.
- **Current:** EWMA(35d span) blended 70/30 with a 20-year EWMA of vol (`mixed_vol_calc`).
- **Incision:** HAR structure — linear combo of 1d/5d/22d realized-vol components
  (~15 lines). Optional later: implied-vol blend for instruments with listed vol indices.
- **Evidence:** 2025 realized-vol survey (Financial Innovation, s40854-025-00809-5);
  HAR + wavelet volatility-timing (SSRN 5391928) — low-frequency vol components improve
  portfolio outcomes AND cut turnover (interacts with §5).
- **Note:** `mixed_vol_calc` does NOT apply the quantile vol floor that `robust_vol_calc`
  does (vol.py:91-113) — the slow blend is an implicit floor. Any HAR variant must be
  tested with floor on/off as a factor, not assumed.

## 2. Rule-redundancy pruning before weight estimation

- **Where:** research-side first (battery experiment), then config: the ~40 variations in
  `systems/provided/rob_system/config.yaml` rule set.
- **Incision:** cluster rules by realized forecast correlation; keep cluster
  representatives; compare pruned (~12-15 rules) vs full set on estimation-noise and
  net SR. Config-only change (rule_variations list) if it wins.
- **Evidence:** arXiv 2510.23150 (Oct 2025) "Revisiting the Structure of Trend Premia:
  When Diversification Hides Redundancy" — directly on point: apparent diversification
  across trend speeds/wrappers is substantially redundant.

## 3. Basis-momentum + hedging-pressure rules

- **Where:** new files in `systems/provided/rules/` beside `carry.py` (41 lines — current
  carry = EWMA-smoothed rolldown only). Carry/price contract data already in multiple
  prices; COT data needs a small new `sysdata` source (free CFTC download).
- **Incision:** `basismom.py` (momentum of the basis/slope, Boons–Prado 2019) and
  `hedgepressure.py` (net hedger positioning). Both cross-checked per asset class.
- **Evidence:** 2025 multi-factor commodity work — equal-weight momentum + basis +
  basis-momentum + value + hedging pressure (ex-precious-metals) reached SR ≈ 1.67
  (arXiv 2606.08283); factor structure survey in CFA Institute 2025 ML-in-commodities
  chapter; factor momentum in commodities (Qian 2025, J. Futures Markets).

## 4. HRP for forecast weights — free experiment, config only

- **Where:** `forecast_weight_estimate: method: hrp` — the forecast-weight estimator uses
  the same optimiser registry (`REGISTER_OF_OPTIMISERS`) your HRP is already wired into.
- **Incision:** none. Pure config + battery run. Zero code.
- **Why:** rule-return correlation matrices are exactly the high-dimension noisy case
  HRP was designed for; cheap to test, plausible small win in weight stability.

## 5. Cost-aware buffering

- **Where:** `systems/buffering.py:35-120` — buffer width is currently a uniform config
  fraction (`buffer_size`) of average position.
- **Incision:** scale buffer width per instrument by its SR-cost (already computed in the
  accounts stage): expensive instruments get wider buffers, cheap micros trade freely.
- **Evidence:** turnover reduction compounds with §1's smoother vol input (SSRN 5391928
  found the turnover channel is where vol-timing gains actually materialize).

## 6. Fast-trend sleeve on cheap instruments only

- **Where:** config `rule_variations` per instrument — plumbing exists; fast EWMAC
  (ewmac2_8, ewmac4_16) is typically cost-culled globally.
- **Incision:** enable fast trend only where SR cost < threshold (liquid micros); judge
  as a sleeve, not per-rule.
- **Evidence:** arXiv 2507.15876 (2025) Bayesian CTA replication — short-term trend +
  market beta sleeve had the best risk-adjusted profile over 2020–2025 live window
  (Sharpe/MaxDD ≈ 3.05 vs benchmark 0.27 Return/MaxDD). Post-2020 regimes reward speed;
  costs are the binding constraint, and micros changed the cost math.

## 7. Local-search polish on the dynamic optimiser

- **Where:** `systems/provided/dynamic_small_system_optimise/greedy_algo.py`.
- **Current:** pure greedy integer-position search against cost-penalised tracking error.
- **Incision:** add a 2-opt swap pass after greedy convergence (pairwise position
  perturbations accepted if tracking error drops). Trivial compute, closes a known chunk
  of greedy's optimality gap. Matters once instrument count grows past ~50 (Norgate gate).

## 8. Regime/ML forecast conditioning — LAST, and gauntlet-shackled

- **Where:** research-only until proven; would plug in as a forecast-weight modifier in
  `systems/forecast_combine.py` (get_combined_forecast, line 55+).
- **Evidence:** XGB/NB filters on trend entries show promise (SSRN 5205525); TSMOM
  remains the strongest single feature in ML studies (CFA 2025). But this is the
  highest-overfit-risk item on the list — purged CV + deflated Sharpe mandatory,
  monotonicity constraints, and a pre-registered kill criterion before the first run.

## Explicitly rejected

- Core rewrites, async/microservices, replacing Mongo, GUI (see upgrade philosophy in
  `.handoffs/pysystemtrade-trading-program.md`).
- LSTM/deep price forecasting (E-TRENDS-style): wrong data regime at daily frequency
  for ~100 instruments; breadth is unavailable, overfit is guaranteed at this scale.

## Sequencing

§1 + §4 (days, near-zero code) → §2 + §5 (weeks, config + one module) → §3 (new data +
rules) → §6 (after cost audit on micros) → §7 (after Norgate) → §8 (only after everything
above is settled and the gauntlet is fully armed). Anything generically useful goes
upstream as a PR (starting with the HRP optimiser itself).
