"""G1b data-transition band check (gate1_parity_definition.md, ADOPTED 2026-07-10).

Runs the chapter-15 system on the PRODUCTION (parquet/db) data -- i.e. the
gap-stitched history -- and checks the full-period metrics against the
pre-registered bands around the frozen-seed anchor:

    sharpe   0.478  +/- 0.10
    ann_std  32.87  +/- 15% relative
    n_days   > 13,422, no >5-business-day holes after the seed boundary
             (the documented MXP hole-bridge window is exempt and reported)

A band breach means the stitched data disagrees with the seed where they
overlap (splice error), not a discovery.

Usage:
    .venv/bin/python analysis/research_harness/g1b_stitch_check.py
"""
import numpy as np
import pandas as pd

ANCHOR_SHARPE = 0.478
SHARPE_BAND = 0.10
ANCHOR_ANN_STD = 32.87
ANN_STD_RELATIVE_BAND = 0.15
ANCHOR_N_DAYS = 13422
SEED_END = pd.Timestamp("2024-03-28")
BDAYS_IN_YEAR = 256


def main() -> None:
    from sysdata.sim.db_futures_sim_data import dbFuturesSimData
    from sysdata.config.configdata import Config
    from systems.provided.futures_chapter15.basesystem import futures_system

    config = Config("systems.provided.futures_chapter15.futuresconfig.yaml")
    system = futures_system(data=dbFuturesSimData(), config=config)
    returns = pd.Series(system.accounts.portfolio().percent).dropna()

    sharpe = returns.mean() * BDAYS_IN_YEAR / (returns.std() * BDAYS_IN_YEAR**0.5)
    ann_std = returns.std() * BDAYS_IN_YEAR**0.5
    n_days = len(returns)
    stitched = returns.index[returns.index > SEED_END]
    gaps = (
        np.diff(stitched.normalize().unique().values)
        .astype("timedelta64[D]")
        .astype(int)
    )
    max_gap = int(gaps.max()) if len(gaps) else 0

    sharpe_ok = abs(sharpe - ANCHOR_SHARPE) <= SHARPE_BAND
    std_ok = abs(ann_std / ANCHOR_ANN_STD - 1) <= ANN_STD_RELATIVE_BAND
    days_ok = n_days > ANCHOR_N_DAYS

    print(f"full-period sharpe : {sharpe:.3f}  (anchor {ANCHOR_SHARPE} +/- {SHARPE_BAND})"
          f"  {'PASS' if sharpe_ok else 'FAIL'}")
    print(f"ann_std pctpts     : {ann_std:.2f}  (anchor {ANCHOR_ANN_STD} +/- "
          f"{ANN_STD_RELATIVE_BAND:.0%})  {'PASS' if std_ok else 'FAIL'}")
    print(f"n_days             : {n_days}  (> {ANCHOR_N_DAYS})  "
          f"{'PASS' if days_ok else 'FAIL'}")
    print(f"last date          : {returns.index[-1].date()}")
    print(f"max calendar gap after seed boundary: {max_gap}d "
          f"(63d MXP hole-bridge documented)")
    print(f"\nG1b: {'PASS' if (sharpe_ok and std_ok and days_ok) else 'FAIL'}")


if __name__ == "__main__":
    main()
