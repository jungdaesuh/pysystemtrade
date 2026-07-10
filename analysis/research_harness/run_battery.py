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
    .venv/bin/python analysis/research_harness/run_battery.py \
        --variants baseline equal --jobs 2 --bootstrap 500 --walkforward 10
    .venv/bin/python analysis/research_harness/run_battery.py \
        --variants baseline handcraft --jobs 2 --vol-func robust_vol_calc

--bootstrap N runs a PAIRED stationary block bootstrap (Politis-Romano) on the
common sample of all variants: same resampled days applied to every variant, so
the confidence interval is on the Sharpe DIFFERENCE vs the first listed variant,
with cross-variant correlation preserved. A difference whose 95% CI straddles 0
is noise, not a finding.

--walkforward N adds a regime-robustness table: rolling N-year windows stepped 1
year over the common aligned sample, reporting for each non-base variant the
mean and worst per-window Sharpe difference vs base and the fraction of windows
it wins. A variant can win the full sample yet be worst in a regime (HRP won the
52yr full sample but was worst in the 2020s), which the full-period bootstrap
alone cannot see. The 95% CI on the MEAN window diff is a stationary block
bootstrap of the VECTOR of per-window diffs (NOT of daily returns): consecutive
rolling windows share N-1 years and are strongly autocorrelated, so blocks (mean
length = N windows, the overlap span) absorb that dependence, and the same
resampled window indices hit every variant (paired). This targets across-regime
variability — the quantity robustness turns on. When fewer than ~4
non-overlapping windows fit the sample, the CI is OMITTED (NaN + caveat)
rather than reported: with so little independent information the block
bootstrap degenerates into mean-preserving full rotations and the CI would be
falsely narrow. Reuses --bootstrap for the rep count and --seed; no CI is
emitted when --bootstrap is 0.

--vol-func NAME swaps the volatility estimator for ALL variants by setting
config.volatility_calculation = dict(func="sysquant.estimators.vol.<NAME>")
(e.g. simple_vol_calc, robust_vol_calc, har_vol_calc); the missing sub-keys
(days, min_periods, ...) are backfilled from defaults.yaml. The func is recorded
in the run directory name and a vol_func column so runs are distinguishable.
Changing the estimator changes position sizing and hence every metric, so a
--vol-func run is NOT comparable to the reference baseline below.

Variants toggle instrument-weight estimation method (exercises the custom HRP
optimiser end-to-end via the config `method:` key -> REGISTER_OF_OPTIMISERS).
`fw_*` variants instead toggle FORECAST-weight estimation (same optimiser
registry, applied across trading rules per instrument; instrument weights stay
fixed) — a single-axis experiment orthogonal to the instrument-weight variants.
Estimated variants are much slower than baseline: expect minutes-to-hours each.

Metrics convention: pysystemtrade `.percent` curves are ADDITIVE percent-of-
capital points (fixed notional capital), so cumulative and drawdown figures can
exceed 100 and are NOT compounded percentages — hence `_pctpts` column names.
Reference values (baseline, default vol estimator, run 2026-07-06): full-period
sharpe 0.478, ann_std 32.9 pctpts, n_days 13422. A materially different baseline
after a code/data change indicates a regression, not a discovery.

Output: results/research_battery/<run-tag>/metrics.csv
"""
import argparse
import datetime
from concurrent.futures import ProcessPoolExecutor
from functools import partial
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


def _fw_estimated(method: str) -> dict:
    return dict(
        use_forecast_weight_estimates=True,
        use_forecast_div_mult_estimates=True,
        forecast_weight_estimate=dict(method=method, date_method="expanding"),
    )


VARIANTS = dict(
    baseline=dict(),
    handcraft=_estimated("handcraft"),
    shrinkage=_estimated("shrinkage"),
    hrp=_estimated("hrp"),
    equal=_estimated("equal_weights"),
    fw_handcraft=_fw_estimated("handcraft"),
    fw_shrinkage=_fw_estimated("shrinkage"),
    fw_hrp=_fw_estimated("hrp"),
    fw_equal=_fw_estimated("equal_weights"),
)


def run_variant(name: str, vol_func: str | None = None) -> pd.Series:
    """Build and run one system; return daily percent returns. Top-level for spawn."""
    from sysdata.config.configdata import Config
    from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
    from systems.provided.futures_chapter15.basesystem import futures_system

    config = Config(CONFIG_PATH)
    for key, value in VARIANTS[name].items():
        setattr(config, key, value)
    if vol_func is not None:
        config.volatility_calculation = dict(func=f"sysquant.estimators.vol.{vol_func}")
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


def stationary_bootstrap_indices(
    n: int, mean_block: float, rng: np.random.Generator
) -> np.ndarray:
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
        sharpes[b] = _ann_sharpe(take)
    diffs = sharpes - sharpes[:, [0]]
    base = aligned.columns[0]
    point = aligned.mean() / aligned.std(ddof=1) * np.sqrt(BDAYS_IN_YEAR)
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


def _ann_sharpe(returns: np.ndarray) -> np.ndarray:
    """Annualised Sharpe per column of a 2-D daily-returns array."""
    return returns.mean(axis=0) / returns.std(axis=0, ddof=1) * np.sqrt(BDAYS_IN_YEAR)


def walkforward_sharpe_differences(
    aligned: pd.DataFrame, window_years: int, n_boot: int, seed: int
) -> pd.DataFrame:
    """Rolling `window_years`-year Sharpe diffs vs the FIRST column, stepped 1 year.

    Each window's diff is base-relative and measured on identical calendar days,
    so cross-variant correlation is embedded in the diff itself. Consecutive
    windows overlap by window_years-1 years and are strongly autocorrelated, so
    the 95% CI on the MEAN window diff is a stationary block bootstrap of the
    VECTOR of per-window diffs (mean block = window_years, the overlap span),
    with the same resampled window indices applied to every variant (paired).
    This measures across-regime variability, which is what robustness turns on.

    CI gate: when fewer than ~4 non-overlapping windows fit the sample
    (n_eff = (n_windows + window_years - 1) / window_years < 4), the CI is
    omitted (NaN + printed caveat). With so little independent information a
    block bootstrap degenerates into full circular rotations, which preserve
    the mean exactly and collapse the CI to a falsely NARROW point mass — the
    anticonservative failure. No CI beats a fake one.
    Empty frame when the aligned sample is shorter than one full window.
    """
    base = aligned.columns[0]
    others = [c for c in aligned.columns if c != base]
    windows = (
        aligned.loc[f"{y}-01-01":f"{y + window_years - 1}-12-31"]
        for y in range(aligned.index[0].year, aligned.index[-1].year - window_years + 2)
    )
    sharpes = [
        pd.Series(_ann_sharpe(w.to_numpy()), index=aligned.columns)
        for w in windows
        if len(w) >= BDAYS_IN_YEAR
    ]
    if not sharpes:
        return pd.DataFrame()
    diffs = pd.DataFrame([s[others] - s[base] for s in sharpes], columns=others)

    dm = diffs.to_numpy()
    nw = len(diffs)
    n_eff = (nw + window_years - 1) / window_years
    if n_boot and n_eff >= 4:
        rng = np.random.default_rng(seed)
        boot = np.array(
            [
                dm[stationary_bootstrap_indices(nw, float(window_years), rng)].mean(
                    axis=0
                )
                for _ in range(n_boot)
            ]
        )
        lo = np.percentile(boot, 2.5, axis=0)
        hi = np.percentile(boot, 97.5, axis=0)
    else:
        if n_boot:
            print(
                f"walkforward: insufficient non-overlapping windows for a CI "
                f"({nw} windows of {window_years}y = {n_eff:.1f} independent; need >= 4)"
                f" — CI omitted"
            )
        lo = hi = np.full(len(others), np.nan)

    rows = [
        dict(
            variant=col,
            n_windows=nw,
            mean_window_diff=round(dm[:, i].mean(), 3),
            worst_window_diff=round(dm[:, i].min(), 3),
            frac_windows_positive=round((dm[:, i] > 0).mean(), 3),
            ci95_lo=round(float(lo[i]), 3),
            ci95_hi=round(float(hi[i]), 3),
        )
        for i, col in enumerate(others)
    ]
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--variants", nargs="+", default=["baseline"], choices=sorted(VARIANTS)
    )
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument(
        "--bootstrap", type=int, default=0, help="bootstrap replicates (0=off)"
    )
    parser.add_argument(
        "--block-days", type=float, default=25.0, help="mean bootstrap block length"
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--walkforward",
        type=int,
        default=0,
        help="rolling window length in years for the regime-robustness table (0=off)",
    )
    parser.add_argument(
        "--vol-func",
        default=None,
        help="volatility estimator in sysquant.estimators.vol applied to all variants",
    )
    args = parser.parse_args()

    worker = (
        run_variant
        if args.vol_func is None
        else partial(run_variant, vol_func=args.vol_func)
    )
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        curves = dict(zip(args.variants, pool.map(worker, args.variants)))

    rows = [
        dict(variant=variant, window=window_name, **metrics)
        for variant, curve in curves.items()
        for window_name, start, end in WINDOWS
        if (metrics := window_metrics(curve, start, end)) is not None
    ]

    run_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.vol_func:
        run_tag = f"{run_tag}_vol-{args.vol_func}"
    out_dir = Path("results/research_battery") / run_tag
    out_dir.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(rows)
    if args.vol_func:
        table.insert(0, "vol_func", args.vol_func)
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

    if args.walkforward and len(args.variants) > 1:
        wf_table = walkforward_sharpe_differences(
            aligned, args.walkforward, n_boot=args.bootstrap, seed=args.seed
        )
        if wf_table.empty:
            print(
                f"\nwalk-forward skipped: aligned sample "
                f"({len(aligned)} days) shorter than one {args.walkforward}y window"
            )
        else:
            if args.vol_func:
                wf_table.insert(0, "vol_func", args.vol_func)
            wf_table.to_csv(out_dir / "walkforward.csv", index=False)
            base = aligned.columns[0]
            print(
                f"\nWalk-forward robustness — rolling {args.walkforward}y windows "
                f"(step 1y) over {len(aligned)} common days; per-window Sharpe diff "
                f"vs '{base}', 95% CI on the mean from a block bootstrap of the "
                f"window diffs ({args.bootstrap} reps, seed {args.seed}):"
            )
            print(wf_table.to_string(index=False))
            print(f"written: {out_dir / 'walkforward.csv'}")


if __name__ == "__main__":
    main()
