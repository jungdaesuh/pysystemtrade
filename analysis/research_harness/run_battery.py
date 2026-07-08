"""Parallel research battery for pysystemtrade backtests.

Runs system variants concurrently (one process per variant), slices each
account curve into evaluation windows, and writes one metrics table. Designed
to saturate a many-core machine without any AI in the loop.

Usage (from repo root, inside the pinned venv):
    .venv/bin/python analysis/research_harness/run_battery.py                    # baseline only, quick
    .venv/bin/python analysis/research_harness/run_battery.py \
        --variants baseline handcraft shrinkage hrp --jobs 4
    .venv/bin/python analysis/research_harness/run_battery.py \
        --variants baseline handcraft shrinkage hrp equal --jobs 5 --bootstrap 2000

--bootstrap N runs a PAIRED stationary block bootstrap (Politis-Romano) on the
common sample of all variants: same resampled days applied to every variant, so
the confidence interval is on the Sharpe DIFFERENCE vs the first listed variant,
with cross-variant correlation preserved. A difference whose 95% CI straddles 0
is noise, not a finding.

Variants toggle instrument-weight estimation method (exercises the custom HRP
optimiser end-to-end via the config `method:` key -> REGISTER_OF_OPTIMISERS).
Estimated variants are much slower than baseline: expect minutes-to-hours each.

Metrics convention: pysystemtrade `.percent` curves are ADDITIVE percent-of-
capital points (fixed notional capital), so cumulative and drawdown figures can
exceed 100 and are NOT compounded percentages — hence `_pctpts` column names.
Reference values (baseline, run 2026-07-06): full-period sharpe 0.478,
ann_std 32.9 pctpts, n_days 13422. A materially different baseline after a
code/data change indicates a regression, not a discovery.

Output: results/research_battery/<run-tag>/metrics.csv
"""
import argparse
import datetime
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
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
        ann_return_pctpts=round(s.mean() * BDAYS_IN_YEAR, 2),
        ann_std_pctpts=round(ann_std, 2),
        sharpe=round(s.mean() * BDAYS_IN_YEAR / ann_std, 3),
        worst_drawdown_pctpts=round((cum - cum.cummax()).min(), 2),
        n_days=len(s),
    )


def stationary_bootstrap_indices(n: int, mean_block: float, rng: np.random.Generator) -> np.ndarray:
    """Politis-Romano stationary bootstrap: circular blocks of geometric length."""
    idx = np.empty(n, dtype=np.int64)
    pos = 0
    while pos < n:
        start = rng.integers(0, n)
        length = min(int(rng.geometric(1.0 / mean_block)), n - pos)
        idx[pos : pos + length] = (start + np.arange(length)) % n
        pos += length
    return idx


def bootstrap_sharpe_differences(
    aligned: pd.DataFrame, n_boot: int, mean_block: float, seed: int
) -> pd.DataFrame:
    """Paired bootstrap: CI on each variant's Sharpe minus the FIRST column's Sharpe."""
    rng = np.random.default_rng(seed)
    arr = aligned.to_numpy()
    n = len(aligned)
    sharpes = np.empty((n_boot, arr.shape[1]))
    for b in range(n_boot):
        take = arr[stationary_bootstrap_indices(n, mean_block, rng)]
        sharpes[b] = take.mean(axis=0) / take.std(axis=0, ddof=1) * np.sqrt(BDAYS_IN_YEAR)
    diffs = sharpes - sharpes[:, [0]]
    base = aligned.columns[0]
    point = (
        aligned.mean() / aligned.std(ddof=1) * np.sqrt(BDAYS_IN_YEAR)
    )
    rows = [
        dict(
            variant=col,
            sharpe_common_window=round(point[col], 3),
            sharpe_diff_vs_base=round(point[col] - point[base], 3),
            ci95_lo=round(np.percentile(diffs[:, i], 2.5), 3),
            ci95_hi=round(np.percentile(diffs[:, i], 97.5), 3),
            prob_beats_base=round((diffs[:, i] > 0).mean(), 3),
        )
        for i, col in enumerate(aligned.columns)
        if col != base
    ]
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variants", nargs="+", default=["baseline"], choices=sorted(VARIANTS))
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--bootstrap", type=int, default=0, help="bootstrap replicates (0=off)")
    parser.add_argument("--block-days", type=float, default=25.0, help="mean bootstrap block length")
    parser.add_argument("--seed", type=int, default=42)
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

    aligned = pd.concat(curves, axis=1).dropna()
    aligned.to_csv(out_dir / "curves.csv")

    if args.bootstrap and len(args.variants) > 1:
        ci_table = bootstrap_sharpe_differences(
            aligned, n_boot=args.bootstrap, mean_block=args.block_days, seed=args.seed
        )
        ci_table.to_csv(out_dir / "bootstrap_ci.csv", index=False)
        base = aligned.columns[0]
        print(
            f"\nPaired stationary block bootstrap ({args.bootstrap} reps, "
            f"mean block {args.block_days:.0f}d, seed {args.seed}) — "
            f"Sharpe difference vs '{base}' on common sample of {len(aligned)} days:"
        )
        print(ci_table.to_string(index=False))
        print(f"written: {out_dir / 'bootstrap_ci.csv'}")


if __name__ == "__main__":
    main()
