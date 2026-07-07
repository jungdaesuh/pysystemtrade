# Personal Portfolio Policy — Systematic Barbell

**Status:** Active
**Last updated:** 2026-07-06
**Owner:** SJD
**Review:** annually on July 1 (next: 2027-07-01). Nothing structural changes between reviews.

## Purpose

The single reference for how capital is allocated and risked. Every position must trace
to a rule in this document or in the system configs it points to. Amendments happen at
the annual review, or after a triggered kill criterion — never mid-year on discretion.

## Structure

### Phase 1 — Defensive base (live from July 2026)

| Sleeve | Target | Implementation | Rule |
|---|---|---|---|
| Floor | 55% | SGOV or 3-month T-bill ladder | hold to maturity / roll |
| Harvest | 35% | 10% US equities, 10% ex-US developed, 8% gold, 7% intermediate Treasuries | rebalance ONLY when a sleeve drifts ±20% relative from target |
| Engine reserve | 10% | cash alongside floor | deploys in Phase 3 |

### Phase 3 — Engine (from ~Sept 2026, strictly gated)

pysystemtrade live on micro futures: **20% of capital, 25% vol target on the sleeve**
(~5 vol points at portfolio level). Rule weighting: carry + mean-reversion weighted up
vs. default trend-heavy mix pending walk-forward evidence (`analysis/research_harness/`).

Gates (all three must pass before any live order):
1. **Parity**: backtest reproduces Rob Carver's published results within tolerance (TODO.md Phase 1.5).
2. **Paper**: 10 consecutive paper-trading days with zero-break reconcile reports.
3. **Capital**: minimum-capital report confirms funding clears cost drag for the chosen universe.

### Phase 4 — Optional layers (only after one clean live quarter)

- **Condors**: XSP iron condors, 5–10% of capital. Entry only if VIX > 18 AND VIX term
  structure not inverted. Defined-risk always. Pending tax-status confirmation (W-9 vs W-8BEN).
- **Convexity pocket**: 2–3%, pre-identified asymmetric positions. Funded only with
  mentally-expensed capital.

## The Five Rules

1. **No position exists without a written rule that produced it.**
2. **Rebalance on bands, never on news.**
3. **The engine scales on evidence, not conviction**: start 20%, +5pp per clean quarter
   (live tracking error within tolerance of paper), hard cap 35%. A bad quarter pauses
   scaling; it never triggers manual overrides.
4. **Kill criteria are pre-registered** (below). Deciding them calm and unpositioned is the point.
5. **Structure changes once a year, on the review date.** Mid-year urges are noise by definition.

## Kill criteria (pre-registered 2026-07-06)

| Trigger | Action |
|---|---|
| Reconciliation break unresolved > 24h | Flatten engine positions, halt engine until root-caused |
| Live vs paper tracking error > 2× expected for a month | Halt engine, investigate before restart |
| Engine sleeve drawdown > 1.25× worst backtest drawdown | Halt engine, full review |
| Condor sleeve monthly loss > 2× premium collected that month | Suspend layer until annual review |
| Any manual override of a system decision | Mandatory written post-mortem before the next trade |

## Agreed expectations (so future-me doesn't re-litigate)

Blended target 9–14%/yr; worst realistic year ≈ −10 to −15%; engine sleeve alone can draw
down 30%+ — that is the purchase price, not a malfunction. The structure is designed to
survive being wrong about any single market view, including the 2026 chop thesis.

## Standing constraints

- J-1 / IBKR residency dependency: all custom code stays broker-portable behind `sysbrokers/` abstractions.
- Production trading never runs on the research machine.
- Secrets: private config in `PYSYS_PRIVATE_CONFIG_DIR`; nothing sensitive in this repo.
- No leverage that can force liquidation of the base; no undefined-risk options; no leveraged/inverse VIX products; no discretionary crypto.
