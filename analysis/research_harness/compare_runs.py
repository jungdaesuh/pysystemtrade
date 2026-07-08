"""Paired comparison of two archived research-battery runs.

Aligns the daily percent-of-capital curves of every variant the two runs share
and reuses run_battery's paired stationary-block bootstrap and walk-forward
machinery, so the statistics are identical to the in-run CIs. Positive diff =
the OTHER run beats the BASE run. Results print and are archived as
``compare_vs_<base_run_name>.csv`` inside the other run's directory.

Usage:
    .venv/bin/python analysis/research_harness/compare_runs.py \
        results/research_battery/<base_run> results/research_battery/<other_run> \
        --bootstrap 2000 --walkforward 10
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from run_battery import (
    BDAYS_IN_YEAR,
    bootstrap_sharpe_differences,
    walkforward_sharpe_differences,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("base_run", type=Path)
    parser.add_argument("other_run", type=Path)
    parser.add_argument(
        "--bootstrap", type=int, default=2000, help="bootstrap replicates"
    )
    parser.add_argument(
        "--walkforward",
        type=int,
        default=0,
        help="rolling window length in years for the regime table (0=off)",
    )
    parser.add_argument(
        "--block-days", type=float, default=25.0, help="mean bootstrap block length"
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    base = pd.read_csv(args.base_run / "curves.csv", index_col=0, parse_dates=True)
    other = pd.read_csv(args.other_run / "curves.csv", index_col=0, parse_dates=True)
    variants = [col for col in base.columns if col in other.columns]
    common = base.index.intersection(other.index)
    print(
        f"common window {common[0].date()}..{common[-1].date()}"
        f" ({len(common)} days); shared variants: {variants}"
    )

    rows = []
    for variant in variants:
        aligned = pd.DataFrame(
            {"base": base.loc[common, variant], "other": other.loc[common, variant]}
        ).dropna()
        point = aligned.mean() / aligned.std(ddof=1) * np.sqrt(BDAYS_IN_YEAR)
        ci = bootstrap_sharpe_differences(
            aligned, n_boot=args.bootstrap, mean_block=args.block_days, seed=args.seed
        ).iloc[0]
        row = dict(
            variant=variant,
            sharpe_base=round(point["base"], 3),
            sharpe_other=round(point["other"], 3),
            sharpe_diff=ci["sharpe_diff_vs_base"],
            ci95_lo=ci["ci95_lo"],
            ci95_hi=ci["ci95_hi"],
            prob_other_beats_base=ci["prob_beats_base"],
        )
        if args.walkforward:
            wf = walkforward_sharpe_differences(
                aligned,
                window_years=args.walkforward,
                n_boot=args.bootstrap,
                seed=args.seed,
            )
            if not wf.empty:
                wf = wf.iloc[0]
                row.update(
                    wf_n_windows=wf["n_windows"],
                    wf_mean_diff=wf["mean_window_diff"],
                    wf_worst_diff=wf["worst_window_diff"],
                    wf_frac_positive=wf["frac_windows_positive"],
                    wf_ci95_lo=wf["ci95_lo"],
                    wf_ci95_hi=wf["ci95_hi"],
                )
        rows.append(row)

    table = pd.DataFrame(rows)
    print(table.to_string(index=False))
    out_path = args.other_run / f"compare_vs_{args.base_run.name}.csv"
    table.to_csv(out_path, index=False)
    print(f"written: {out_path}")


if __name__ == "__main__":
    main()
