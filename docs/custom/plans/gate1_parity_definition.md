# Gate 1 — Parity Definition (ADOPTED)

> Status: ADOPTED as written 2026-07-10 (user decision, logged in
> `docs/custom/DECISIONS.md`). G1a passing; G1c script to be written;
> G1b arms when the gap-stitch lands.

## Why the original formulation is unfalsifiable

Gate 1 was originally "our backtest reproduces Rob Carver's published figures within
tolerance". That cannot be made operational:

- **No target figures exist in-repo.** `TODO.md` Phase 1.5 planned a "parity report
  against blog figures" but never recorded which figures.
- **Universe mismatch.** Published full-system numbers come from a 40–100 instrument
  universe; the shipped chapter-15 config trades six (CORN, EUROSTX, MXP, SOFR, US10,
  V2X). A hierarchical/diversified system's Sharpe rises with breadth, so the six-
  instrument system structurally cannot match full-system figures — a gap that says
  nothing about our code being right.
- **Vintage mismatch.** Published figures use different data end-dates, cost
  assumptions, and code versions (the framework has evolved for a decade).

Chasing figure-exact parity against a moving external target would either never pass
or pass by accident. What Gate 1 actually needs to certify: **the machine computes
what the methodology says it should, and we can detect when it stops doing so.**

## Proposed definition — Gate 1 passes when all three hold

### G1a — Deterministic self-parity (regression anchor) — OPERATIONAL today

On the frozen seed dataset (CSV history ending 2024-03-28), the baseline battery
reproduces the reference values EXACTLY (to printed precision):

```
.venv/bin/python analysis/research_harness/run_battery.py --variants baseline --jobs 1
# must print: sharpe 0.478, ann_std 32.87 pctpts, n_days 13422
```

Any deviation after a code change, upstream rebase, or environment change is a
regression, not a discovery. Evidence: any fresh run dir under
`results/research_battery/`. This check has already passed on the Threadripper
(machine-migration acceptance test, 2026-07-08).

### G1b — Data-transition stability bands

When the 2024-03→present gap is closed (stitch or vendor seed), the full-period
metrics move only as much as ~2 extra years on top of ~52 shared years can move them.
Pre-registered acceptance bands on the extended-history baseline run:

| Metric (full period) | Anchor | Band | Rationale |
|---|---|---|---|
| Sharpe | 0.478 | ±0.10 | 2yr/54yr weight ≈ 4%; a larger move implies the new data disagrees with the old where they overlap (splice error), not new information |
| ann_std (pctpts) | 32.87 | ±15% relative | vol targeting should keep realized risk stable across a data extension |
| n_days | 13,422 | strictly greater; no gaps > 5 business days inside the stitched window | continuity check on the splice itself |

A band breach BLOCKS Gate 1 and triggers a splice audit (compare overlapping dates
old-vs-new before suspecting the strategy). Note: realized vol (32.9) exceeding the
configured 20% target is EXPECTED behavior — the instrument diversification
multiplier scales positions assuming imperfect correlations; when correlations run
higher than assumed, realized vol overshoots. Do not "fix" this to force 20.

### G1c — Sim ↔ production methodology parity

Same config + same data through both code paths:

- Sim path: `systems.provided.futures_chapter15.basesystem.futures_system`
- Production path: `sysproduction.strategy_code.run_system_classic`
  (`production_classic_futures_system`)

Acceptance: final-day optimal positions per instrument agree within the buffering
band (identical after rounding); any residual difference must be explained line-by-
line (capital handling, FX, cost timing) and recorded. This is the parity that
matters for real money — it certifies the thing placing orders computes the same
answer as the thing we validated for 52 years. Runnable today on the frozen seed
data; does NOT wait for the data-gap decision.

## Universe question — settled by declaration

The **parity universe is the chapter-15 six**, because that is the frozen, shipped
dataset the anchor is defined on. It is explicitly NOT expected to match published
full-system figures. Full-universe validation becomes a new gate criterion only
after the vendor-data decision (which is what unlocks a broad universe), with fresh
pre-registered bands at that time.

## What adopting this changes

- Gate 1 stops being blocked on unrecoverable external figures; G1a already passes,
  G1c is executable now, G1b arms automatically when the data gap closes.
- `TODO.md` Phase 1/1.5 ("GBP base, blog alignment, parity report vs blog figures")
  is superseded — those steps described the pre-reset fork's plan.

## Adoption checklist

- [ ] User reviews bands (esp. G1b Sharpe ±0.10) and the universe declaration
- [ ] Adoption entry in `DECISIONS.md` (template: decision/expectation/judge-on)
- [ ] G1c comparison script written and its first run archived under `results/`
