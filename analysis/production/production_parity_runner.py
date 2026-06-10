#!/usr/bin/env python3
"""Parity runner that drives the production entrypoint against local CSV data."""
from __future__ import annotations

import argparse
import json
import logging
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd

from syscore.dateutils import Frequency, from_frequency_to_times_per_year
from syscore.pandas.strategy_functions import drawdown, turnover
from sysdata.config.configdata import Config


@dataclass
class YearWindow:
    year: int
    start: pd.Timestamp
    end: pd.Timestamp


BUSINESS_DAYS_PER_YEAR = float(from_frequency_to_times_per_year(Frequency.BDay))
CONFIG_PATH = "systems.provided.futures_chapter15.futuresconfig.yaml"
DEFAULTS_PATH = "sysdata.config.defaults.yaml"
DEFAULT_CAPITAL = 1_000_000
DEFAULT_BASE_CCY = "GBP"


def _suppress_verbose_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    for name in ("base_system", "futures_system", "asyncio"):
        logging.getLogger(name).setLevel(logging.WARNING)


def _patch_production_data_to_csv() -> None:
    from sysproduction.data import production_data_objects as prod_objs
    from sysdata.sim import db_futures_sim_data as db_sim
    from sysdata.csv.csv_adjusted_prices import csvFuturesAdjustedPricesData
    from sysdata.csv.csv_multiple_prices import csvFuturesMultiplePricesData
    from sysdata.csv.csv_spot_fx import csvFxPricesData
    from sysdata.csv.csv_instrument_data import csvFuturesInstrumentData
    from sysdata.csv.csv_roll_parameters import csvRollParametersData
    from sysdata.csv.csv_spread_costs import csvSpreadCostData

    csv_mapping = {
        prod_objs.FUTURES_ADJUSTED_PRICE_DATA: csvFuturesAdjustedPricesData,
        prod_objs.FUTURES_MULTIPLE_PRICE_DATA: csvFuturesMultiplePricesData,
        prod_objs.FX_DATA: csvFxPricesData,
        prod_objs.STORED_SPREAD_DATA: csvSpreadCostData,
        prod_objs.FUTURES_INSTRUMENT_DATA: csvFuturesInstrumentData,
        prod_objs.ROLL_PARAMETERS_DATA: csvRollParametersData,
    }

    for key, klass in csv_mapping.items():
        prod_objs.use_production_classes[key] = klass
        if key in db_sim.use_sim_classes:
            db_sim.use_sim_classes[key] = klass


def _build_production_system(
    base_currency: str = DEFAULT_BASE_CCY,
    capital: float = DEFAULT_CAPITAL,
    capital_multiplier: str = "syscore.capital.full_compounding",
    allocator: str = "fixed",
    hrp_linkage: str = "single",
):
    from sysproduction.strategy_code.run_system_classic import (
        production_classic_futures_system,
    )
    from sysdata.sim.csv_futures_sim_data import csvFuturesSimData

    _patch_production_data_to_csv()

    base_config = Config([DEFAULTS_PATH, CONFIG_PATH])
    instrument_weight_estimate = deepcopy(
        getattr(base_config, "instrument_weight_estimate", {})
    )
    use_weight_estimates = bool(
        getattr(base_config, "use_instrument_weight_estimates", False)
    )

    allocator_normalised = allocator.lower()
    if allocator_normalised in {"fixed", "static"}:
        use_weight_estimates = False
    elif allocator_normalised in {"handcraft", "hrp", "equal_weights"}:
        use_weight_estimates = True
        if instrument_weight_estimate:
            instrument_weight_estimate["method"] = allocator_normalised
            if allocator_normalised == "hrp":
                instrument_weight_estimate["linkage_method"] = hrp_linkage
        else:
            instrument_weight_estimate = {
                "func": "sysquant.optimisation.generic_optimiser.genericOptimiser",
                "method": allocator_normalised,
                "date_method": "expanding",
                "rollyears": 20,
                "cleaning": True,
                "apply_cost_weight": False,
            }
            if allocator_normalised == "hrp":
                instrument_weight_estimate["linkage_method"] = hrp_linkage
    else:
        raise ValueError(f"Unsupported allocator '{allocator}'")

    capital_multiplier_dict = {"func": capital_multiplier}

    config_override = {
        "capital_multiplier": capital_multiplier_dict,
        "vol_normalise_currency_costs": True,
        "use_instrument_weight_estimates": use_weight_estimates,
    }

    if instrument_weight_estimate:
        config_override["instrument_weight_estimate"] = instrument_weight_estimate

    csv_data = csvFuturesSimData()
    system = production_classic_futures_system(
        csv_data.data,
        [CONFIG_PATH, config_override],
        base_currency=base_currency,
        notional_trading_capital=capital,
    )
    return system


def _validate_instrument_universe(system) -> None:
    instruments = system.get_instrument_list()
    clean_free = [code for code in instruments if code.endswith("_CLEAN")]
    if clean_free:
        raise RuntimeError(
            "Detected *_CLEAN proxies in instrument universe: " + ", ".join(clean_free)
        )


def _business_day_filter(series: pd.Series) -> pd.Series:
    if not isinstance(series.index, pd.DatetimeIndex):
        series.index = pd.to_datetime(series.index)
    weekday_mask = series.index.dayofweek < 5
    return series.loc[weekday_mask]


def _slice_series(series: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    sliced = series.loc[start:end]
    if not isinstance(sliced.index, pd.DatetimeIndex):
        sliced.index = pd.to_datetime(sliced.index)
    return sliced


def _compute_return_metrics(series: pd.Series) -> Dict[str, float]:
    cleaned = (series / 100.0).dropna()
    if cleaned.empty:
        return {
            "trading_days": 0,
            "ann_vol": float("nan"),
            "ann_return": float("nan"),
            "sharpe": float("nan"),
            "cagr": float("nan"),
            "total_return": float("nan"),
            "worst_drawdown": float("nan"),
        }

    trading_days = float(len(cleaned))
    daily_mean = float(cleaned.mean())
    daily_std = float(cleaned.std(ddof=1))
    ann_return = daily_mean * BUSINESS_DAYS_PER_YEAR
    ann_vol = daily_std * np.sqrt(BUSINESS_DAYS_PER_YEAR)
    sharpe = float("nan") if ann_vol == 0 else ann_return / ann_vol

    gross_curve = (1.0 + cleaned).cumprod()
    total_return = float(gross_curve.iloc[-1] - 1.0)
    years_in_sample = (
        trading_days / BUSINESS_DAYS_PER_YEAR if trading_days else float("nan")
    )
    if years_in_sample and years_in_sample > 0 and gross_curve.iloc[-1] > 0:
        cagr = float(gross_curve.iloc[-1] ** (1.0 / years_in_sample) - 1.0)
    else:
        cagr = float("nan")
    worst_dd = float(drawdown(gross_curve).min())

    return {
        "trading_days": trading_days,
        "ann_vol": ann_vol,
        "ann_return": ann_return,
        "sharpe": sharpe,
        "cagr": cagr,
        "total_return": total_return,
        "worst_drawdown": worst_dd,
    }


def _compute_turnover_for_window(
    system,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> float:
    total = 0.0
    instruments = system.get_instrument_list()
    for instrument in instruments:
        positions = system.accounts.get_buffered_position(instrument)
        avg_position = (
            system.accounts.get_average_position_for_instrument_at_portfolio_level(
                instrument
            )
        )
        positions_window = _slice_series(positions, start, end)
        avg_window = _slice_series(avg_position, start, end)
        if positions_window.empty:
            continue
        value = float(turnover(positions_window, avg_window))
        if np.isnan(value):
            continue
        total += value
    return total


def _export_curves(
    curve,
    year_window: YearWindow,
    output_dir: Path,
) -> Tuple[pd.Series, pd.Series, Path, Path]:
    percent = pd.Series(curve.percent)
    value_terms = pd.Series(curve.value_terms)

    percent_slice = _business_day_filter(
        _slice_series(percent, year_window.start, year_window.end)
    )
    value_slice = _business_day_filter(
        _slice_series(value_terms, year_window.start, year_window.end)
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    percent_path = output_dir / f"production_parity_{year_window.year}_percent.csv"
    value_path = output_dir / f"production_parity_{year_window.year}_value_terms.csv"

    percent_slice.to_frame(name="daily_return").to_csv(percent_path, index_label="date")
    value_slice.to_frame(name="account_value").to_csv(value_path, index_label="date")

    return percent_slice, value_slice, percent_path, value_path


def _build_year_windows(years: Iterable[int]) -> List[YearWindow]:
    windows: List[YearWindow] = []
    for year in years:
        start = pd.Timestamp(f"{year}-01-01")
        end = pd.Timestamp(f"{year}-12-31")
        if year == pd.Timestamp.today().year:
            end = min(end, pd.Timestamp.today())
        windows.append(YearWindow(year=year, start=start, end=end))
    return windows


def _normalise_capital_multiplier(name: str) -> str:
    trimmed = name.strip()
    if "." in trimmed:
        return trimmed
    return f"syscore.capital.{trimmed.lower()}"


def run_parity(
    years: Iterable[int],
    output_root: Path,
    base_currency: str = DEFAULT_BASE_CCY,
    capital: float = DEFAULT_CAPITAL,
    capital_multiplier: str = "syscore.capital.full_compounding",
    allocator: str = "fixed",
    hrp_linkage: str = "single",
) -> Dict[int, Dict[str, float]]:
    _suppress_verbose_logging()
    system = _build_production_system(
        base_currency=base_currency,
        capital=capital,
        capital_multiplier=capital_multiplier,
        allocator=allocator,
        hrp_linkage=hrp_linkage,
    )
    _validate_instrument_universe(system)

    curve = system.accounts.portfolio()
    windows = _build_year_windows(years)

    metrics_by_year: Dict[int, Dict[str, float]] = {}
    for window in windows:
        percent_series, value_series, percent_path, value_path = _export_curves(
            curve=curve,
            year_window=window,
            output_dir=output_root / str(window.year),
        )

        metrics = _compute_return_metrics(percent_series)
        turnover_value = _compute_turnover_for_window(
            system=system,
            start=window.start,
            end=window.end,
        )
        metrics.update(
            {
                "start_date": str(percent_series.index.min())
                if not percent_series.empty
                else None,
                "end_date": str(percent_series.index.max())
                if not percent_series.empty
                else None,
                "turnover": turnover_value,
                "percent_path": str(percent_path),
                "value_path": str(value_path),
            }
        )

        metrics_path = percent_path.with_name(
            f"production_parity_{window.year}_metrics.json"
        )
        with open(metrics_path, "w", encoding="utf-8") as handle:
            json.dump(metrics, handle, indent=2)

        metrics_by_year[window.year] = metrics

    return metrics_by_year


def _parse_years(raw: Iterable[str]) -> List[int]:
    years: List[int] = []
    for item in raw:
        if item.lower() == "all":
            years.extend([2024, 2025])
        else:
            years.append(int(item))
    return sorted(set(years))


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate parity outputs via the production entrypoint",
    )
    parser.add_argument(
        "--years",
        nargs="*",
        default=["2024", "2025"],
        help="Years to export (e.g. 2024 2025 or 'all')",
    )
    parser.add_argument(
        "--output-root",
        default="results",
        help="Root directory for results (default: results)",
    )
    parser.add_argument(
        "--base-currency",
        default=DEFAULT_BASE_CCY,
        help="Base currency override (default: GBP)",
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=DEFAULT_CAPITAL,
        help="Notional trading capital (default: 1_000_000)",
    )
    parser.add_argument(
        "--capital-multiplier",
        default="full_compounding",
        help=(
            "Capital multiplier function name (e.g. full_compounding, fixed_capital, "
            "half_compounding, or dotted path such as syscore.capital.full_compounding)"
        ),
    )
    parser.add_argument(
        "--allocator",
        default="fixed",
        help=(
            "Instrument allocator: fixed, handcraft, equal_weights, hrp (default: fixed)"
        ),
    )
    parser.add_argument(
        "--hrp-linkage",
        default="single",
        help="Linkage method for HRP allocator (default: single)",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)
    years = _parse_years(args.years)

    capital_multiplier = _normalise_capital_multiplier(args.capital_multiplier)
    allocator = args.allocator.lower()
    allocator = {"equal": "equal_weights", "static": "fixed"}.get(allocator, allocator)
    hrp_linkage = args.hrp_linkage.lower()

    metrics = run_parity(
        years=years,
        output_root=Path(args.output_root),
        base_currency=args.base_currency,
        capital=args.capital,
        capital_multiplier=capital_multiplier,
        allocator=allocator,
        hrp_linkage=hrp_linkage,
    )

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
