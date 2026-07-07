"""Parallel research battery for pysystemtrade backtests.

Runs system variants concurrently (one process per variant), slices each
account curve into evaluation windows, and writes one metrics table. Designed
to saturate a many-core machine without any AI in the loop.

Usage (from repo root, inside the pinned venv):
    .venv/bin/python analysis/research_harness/run_battery.py                    # baseline only, quick
    .venv/bin/python analysis/research_harness/run_battery.py \
        --variants baseline handcraft shrinkage hrp --jobs 4

Variants toggle instrument-weight estimation method (exercises the custom HRP
optimiser end-to-end via the config `method:` key -> REGISTER_OF_OPTIMISERS).
Estimated variants are much slower than baseline: expect minutes-to-hours each.

Output: results/research_battery/<run-tag>/metrics.csv
"""
import argparse
import datetime
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

BDAYS_IN_YEAR = 256
CONFIG_PATH = "systems.provided.futures_chapter15.futuresconfig.yaml"

WINDOWS = [
    ("full", None, None),
    ("1980s", "1980-01-01", "1989-12-31"),
    ("1990s", "1990-01-01", "1999-12-31"),
    ("2000s", "2000-01-01", "2009-12-31"),
    ("2010s", "2010-01-01", "2019-12-31"),
    ("2020s", "2020-01-01", None),
]


def _estimated(method: str) -> dict:
    return dict(
        use_instrument_weight_estimates=True,
        use_instrument_div_mult_estimates=True,
        instrument_weight_estimate=dict(method=method, date_method="expanding"),
    )


VARIANTS = dict(
    baseline=dict(),
    handcraft=_estimated("handcraft"),
    shrinkage=_estimated("shrinkage"),
    hrp=_estimated("hrp"),
    equal=_estimated("equal_weights"),
)


def run_variant(name: str) -> pd.Series:
    """Build and run one system; return daily percent returns. Top-level for spawn."""
    from sysdata.config.configdata import Config
    from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
    from systems.provided.futures_chapter15.basesystem import futures_system

    config = Config(CONFIG_PATH)
    for key, value in VARIANTS[name].items():
        setattr(config, key, value)
    system = futures_system(data=csvFuturesSimData(), config=config)
    return pd.Series(system.accounts.portfolio().percent)


def window_metrics(daily_pct: pd.Series, start, end) -> dict | None:
    s = daily_pct.loc[start:end].dropna()
    if len(s) < BDAYS_IN_YEAR:
        return None
    ann_std = s.std() * BDAYS_IN_YEAR**0.5
    cum = s.cumsum()
    return dict(
        ann_return_pct=round(s.mean() * BDAYS_IN_YEAR, 2),
        ann_std_pct=round(ann_std, 2),
        sharpe=round(s.mean() * BDAYS_IN_YEAR / ann_std, 3),
        worst_drawdown_pct=round((cum - cum.cummax()).min(), 2),
        n_days=len(s),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variants", nargs="+", default=["baseline"], choices=sorted(VARIANTS))
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()

    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        curves = dict(zip(args.variants, pool.map(run_variant, args.variants)))

    rows = [
        dict(variant=variant, window=window_name, **metrics)
        for variant, curve in curves.items()
        for window_name, start, end in WINDOWS
        if (metrics := window_metrics(curve, start, end)) is not None
    ]

    run_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("results/research_battery") / run_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(rows)
    table.to_csv(out_dir / "metrics.csv", index=False)
    print(table.to_string(index=False))
    print(f"\nwritten: {out_dir / 'metrics.csv'}")


if __name__ == "__main__":
    main()
