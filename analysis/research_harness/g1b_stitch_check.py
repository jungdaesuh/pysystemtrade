"""G1b data-transition check, as ADOPTED and AMENDED (2026-07-12).

Implements the adopted criterion faithfully (the original checker tested the
portfolio calendar only and could not fail a pipeline — see DECISIONS
2026-07-12 external-audit entry), hardened after a follow-up audit found the
gap scan alone let an empty or one-point series report continuity OK:

  1. Boundary anchor: every pilot instrument's adjusted price series must have
     at least one observation on/before the seed boundary and at least one
     after (else "no stitched data").
  2. Per-instrument continuity: no gap over 5 BUSINESS days after the seed
     boundary, except windows pre-registered as hole-bridges at stitch time
     (currently exactly one: MXP, the CME FX-migration hole).
  3. Minimum coverage: post-boundary observations must cover >= 90% of the
     business days between the boundary and the series' last date, after
     excluding business days inside exemption windows.
  4. Freshness: each instrument's last date must be within 5 business days of
     the freshest last date across the pilot six.
  5. Portfolio bands vs the frozen-seed anchor: sharpe 0.478 +/- 0.10,
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
MIN_COVERAGE = 0.90
MAX_STALE_BDAYS = 5
BDAYS_IN_YEAR = 256

# Pre-registered hole-bridge exemptions (DECISIONS.md 2026-07-10 gap-stitch entry,
# formalised by the 2026-07-12 G1b amendment). Add entries ONLY via a decision entry.
HOLE_EXEMPTIONS = {
    "MXP": [(pd.Timestamp("2025-03-17"), pd.Timestamp("2025-05-19"))],
}


def continuity_failures(
    dates: pd.DatetimeIndex,
    exemptions: list[tuple[pd.Timestamp, pd.Timestamp]],
) -> list[str]:
    """Pure continuity assertions for one instrument's observation dates.

    Checks the boundary anchor (observations on both sides of SEED_END),
    post-boundary gaps vs MAX_GAP_BDAYS outside the (start, end) `exemptions`
    windows, and MIN_COVERAGE of post-boundary business days (exempt business
    days excluded). Returns human-readable failure strings; empty means pass.
    """
    observed = dates.normalize().unique().sort_values()
    stitched = observed[observed > SEED_END]
    if len(stitched) == 0 or len(stitched) == len(observed):
        return [
            f"no stitched data: {len(observed) - len(stitched)} observations "
            f"on/before {SEED_END.date()}, {len(stitched)} after"
        ]

    failures = []
    for previous, current in zip(stitched[:-1], stitched[1:]):
        gap_bdays = int(np.busday_count(previous.date(), current.date())) - 1
        if gap_bdays <= MAX_GAP_BDAYS:
            continue
        if any(
            start <= previous and current <= end + pd.Timedelta(days=4)
            for start, end in exemptions
        ):
            continue
        failures.append(
            f"{gap_bdays} business days missing "
            f"{previous.date()}..{current.date()} (no exemption)"
        )

    required = pd.bdate_range(SEED_END + pd.Timedelta(days=1), stitched[-1])
    for start, end in exemptions:
        required = required[(required < start) | (required > end)]
    if len(required):
        coverage = required.isin(stitched).mean()
        if coverage < MIN_COVERAGE:
            failures.append(
                f"coverage {coverage:.1%} of {len(required)} non-exempt business "
                f"days {SEED_END.date()}..{stitched[-1].date()} "
                f"(minimum {MIN_COVERAGE:.0%})"
            )
    return failures


def freshness_failures(last_dates: dict[str, pd.Timestamp]) -> list[str]:
    """Pure cross-instrument staleness check on `last_dates` (code -> last
    observation date, non-empty): every instrument must be within
    MAX_STALE_BDAYS business days of the freshest last date. Returns
    human-readable failure strings; empty means pass."""
    freshest = max(last_dates.values())
    failures = []
    for code, last in sorted(last_dates.items()):
        stale_bdays = int(np.busday_count(last.date(), freshest.date()))
        if stale_bdays > MAX_STALE_BDAYS:
            failures.append(
                f"{code} stale: last observation {last.date()} is {stale_bdays} "
                f"business days behind freshest {freshest.date()} "
                f"(max {MAX_STALE_BDAYS})"
            )
    return failures


def main() -> None:
    from sysdata.config.configdata import Config
    from sysdata.data_blob import dataBlob
    from sysdata.sim.db_futures_sim_data import dbFuturesSimData
    from sysproduction.data.prices import diagPrices
    from systems.provided.futures_chapter15.basesystem import futures_system

    print("== per-instrument continuity (adopted criterion) ==")
    failures = []
    last_dates = {}
    with dataBlob(log_name="g1b_check") as data:
        diag = diagPrices(data)
        for code in PILOT_INSTRUMENTS:
            series = pd.Series(diag.get_adjusted_prices(code)).dropna()
            instrument_failures = continuity_failures(
                series.index, HOLE_EXEMPTIONS.get(code, [])
            )
            print(
                f"  {code:10} continuity OK"
                if not instrument_failures
                else f"  {code:10} CONTINUITY VIOLATION"
            )
            failures.extend(f"{code}: {failure}" for failure in instrument_failures)
            if len(series):
                last_dates[code] = series.index.max().normalize()

    print("== cross-instrument freshness ==")
    if last_dates:
        stale = freshness_failures(last_dates)
        print(
            f"  freshest last date {max(last_dates.values()).date()}; "
            + (
                f"all {len(last_dates)} instruments within {MAX_STALE_BDAYS} bdays"
                if not stale
                else f"{len(stale)} STALE"
            )
        )
        failures.extend(stale)

    for failure in failures:
        print(f"  FAIL {failure}")
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
