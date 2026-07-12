"""G1c sim <-> production parity check (gate1_parity_definition.md, ADOPTED).

Builds the chapter-15 system twice on the same production (parquet/db) data:

  sim path        : systems.provided...futures_system(dbFuturesSimData, Config)
  production path : sysproduction.strategy_code.run_system_classic.
                    production_classic_futures_system(dataBlob, config_filename)

and compares, for every pilot instrument, the final-day notional position and
the buffered (rounded) position production would actually hold. The paths
share the backtest engine by construction; what this certifies is that the
PRODUCTION wrapper -- dataBlob wiring, capital/currency overrides, buffering
and rounding -- introduces no divergence. Any residual difference must be
explained line-by-line before Gate 1 can close.

Usage:
    .venv/bin/python analysis/research_harness/g1c_parity_check.py
"""
import numpy as np

CONFIG_FILENAME = "systems.provided.futures_chapter15.futuresconfig.yaml"
PILOT_INSTRUMENTS = ["CORN", "EUROSTX", "MXP", "SOFR", "US10", "V2X"]
TOLERANCE = 1e-6


def final_positions(system, instruments) -> dict:
    positions = {}
    for code in instruments:
        notional = system.portfolio.get_notional_position(code)
        buffers = system.portfolio.get_buffers_for_position(code)
        positions[code] = dict(
            notional=float(notional.ffill().iloc[-1]),
            buffer_top=float(buffers.ffill().iloc[-1, 0]),
            buffer_bottom=float(buffers.ffill().iloc[-1, 1]),
        )
    return positions


def main() -> None:
    from sysdata.config.configdata import Config
    from sysdata.data_blob import dataBlob
    from sysdata.sim.db_futures_sim_data import dbFuturesSimData
    from sysproduction.strategy_code.run_system_classic import (
        production_classic_futures_system,
    )
    from systems.provided.futures_chapter15.basesystem import futures_system

    with dataBlob(log_name="g1c_parity") as data:
        production_system = production_classic_futures_system(data, CONFIG_FILENAME)
        production = final_positions(production_system, PILOT_INSTRUMENTS)

    sim_system = futures_system(data=dbFuturesSimData(), config=Config(CONFIG_FILENAME))
    sim = final_positions(sim_system, PILOT_INSTRUMENTS)

    print(
        f"{'':10}{'sim notional':>14}{'prod notional':>14}{'diff':>12}  buffered band (prod)"
    )
    all_ok = True
    for code in PILOT_INSTRUMENTS:
        diff = production[code]["notional"] - sim[code]["notional"]
        ok = abs(diff) <= TOLERANCE
        all_ok &= ok
        print(
            f"{code:10}{sim[code]['notional']:>14.4f}{production[code]['notional']:>14.4f}"
            f"{diff:>12.2e}  [{production[code]['buffer_bottom']:.2f}, "
            f"{production[code]['buffer_top']:.2f}]  {'OK' if ok else 'DIVERGED'}"
        )

    print(f"\nG1c: {'PASS' if all_ok else 'FAIL'}")
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
