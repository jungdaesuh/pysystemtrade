"""G1b data-transition check, as ADOPTED and AMENDED (2026-07-12).

Implements the adopted criterion faithfully (the original checker tested the
portfolio calendar only and could not fail a pipeline — see DECISIONS
2026-07-12 external-audit entry):

  1. Per-instrument continuity: every pilot instrument's adjusted price series
     must have no gap over 5 BUSINESS days after the seed boundary, except
     windows pre-registered as hole-bridges at stitch time (currently exactly
     one: MXP, the CME FX-migration hole).
  2. Portfolio bands vs the frozen-seed anchor: sharpe 0.478 +/- 0.10,
     ann_std 32.87 +/- 15% relative, n_days > 13,422.

Exits nonzero on any failure so pipelines fail closed.

Usage:
    .venv/bin/python analysis/research_harness/g1b_stitch_check.py
"""
import sys

import numpy as np
import pandas as pd

PILOT_INSTRUMENTS = ["CORN", "EUROSTX", "MXP", "SOFR", "US10", "V2X"]
ANCHOR_SHARPE = 0.478
SHARPE_BAND = 0.10
ANCHOR_ANN_STD = 32.87
ANN_STD_RELATIVE_BAND = 0.15
ANCHOR_N_DAYS = 13422
SEED_END = pd.Timestamp("2024-03-28")
MAX_GAP_BDAYS = 5
BDAYS_IN_YEAR = 256

# Pre-registered hole-bridge exemptions (DECISIONS.md 2026-07-10 gap-stitch entry,
# formalised by the 2026-07-12 G1b amendment). Add entries ONLY via a decision entry.
HOLE_EXEMPTIONS = {
    "MXP": [(pd.Timestamp("2025-03-17"), pd.Timestamp("2025-05-19"))],
}


def instrument_gap_failures(diag) -> list:
    failures = []
    for code in PILOT_INSTRUMENTS:
        series = pd.Series(diag.get_adjusted_prices(code)).dropna()
        stitched = series.index[series.index > SEED_END].normalize().unique()
        exempt = HOLE_EXEMPTIONS.get(code, [])
        worst_allowed = 0
        for previous, current in zip(stitched[:-1], stitched[1:]):
            gap_bdays = int(np.busday_count(previous.date(), current.date())) - 1
            if gap_bdays <= MAX_GAP_BDAYS:
                continue
            if any(
                start <= previous and current <= end + pd.Timedelta(days=4)
                for start, end in exempt
            ):
                worst_allowed = max(worst_allowed, gap_bdays)
                continue
            failures.append((code, previous.date(), current.date(), gap_bdays))
        exempt_note = f" (exempt bridge: {worst_allowed}bd)" if worst_allowed else ""
        print(
            f"  {code:10} continuity OK{exempt_note}"
            if not [f for f in failures if f[0] == code]
            else f"  {code:10} GAP VIOLATION"
        )
    return failures


def main() -> None:
    from sysdata.config.configdata import Config
    from sysdata.data_blob import dataBlob
    from sysdata.sim.db_futures_sim_data import dbFuturesSimData
    from sysproduction.data.prices import diagPrices
    from systems.provided.futures_chapter15.basesystem import futures_system

    print("== per-instrument continuity (adopted criterion) ==")
    with dataBlob(log_name="g1b_check") as data:
        failures = instrument_gap_failures(diagPrices(data))
    for code, start, end, gap in failures:
        print(
            f"  FAIL {code}: {gap} business days missing {start}..{end} (no exemption)"
        )
    continuity_ok = not failures

    print("== portfolio bands vs anchor ==")
    config = Config("systems.provided.futures_chapter15.futuresconfig.yaml")
    system = futures_system(data=dbFuturesSimData(), config=config)
    returns = pd.Series(system.accounts.portfolio().percent).dropna()
    sharpe = returns.mean() * BDAYS_IN_YEAR / (returns.std() * BDAYS_IN_YEAR**0.5)
    ann_std = returns.std() * BDAYS_IN_YEAR**0.5
    n_days = len(returns)

    sharpe_ok = abs(sharpe - ANCHOR_SHARPE) <= SHARPE_BAND
    std_ok = abs(ann_std / ANCHOR_ANN_STD - 1) <= ANN_STD_RELATIVE_BAND
    days_ok = n_days > ANCHOR_N_DAYS
    print(
        f"  sharpe  {sharpe:.3f} (anchor {ANCHOR_SHARPE}+/-{SHARPE_BAND})  "
        f"{'PASS' if sharpe_ok else 'FAIL'}"
    )
    print(
        f"  ann_std {ann_std:.2f} (anchor {ANCHOR_ANN_STD}+/-{ANN_STD_RELATIVE_BAND:.0%})  "
        f"{'PASS' if std_ok else 'FAIL'}"
    )
    print(
        f"  n_days  {n_days} (> {ANCHOR_N_DAYS})  {'PASS' if days_ok else 'FAIL'}  "
        f"last {returns.index[-1].date()}"
    )

    all_ok = continuity_ok and sharpe_ok and std_ok and days_ok
    print(f"\nG1b: {'PASS' if all_ok else 'FAIL'}")
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
