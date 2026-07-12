"""G1c sim <-> production parity, STRENGTHENED per the 2026-07-12 audit.

The original check compared two near-identical in-memory constructions and was
too weak to close a gate. This version compares what production actually
STORED against an independent recomputation:

  stored side  : the buffered optimal positions the Phase-6 production backtest
                 wrote to Mongo (runSystemClassic -> updated_buffered_positions),
                 plus the strategy capital it ran with
  recomputed   : a fresh sim system on the production data at that SAME
                 recorded capital; final-day buffered position bands

Acceptance (adopted criterion): per instrument, the stored band equals the
recomputed band within tolerance, and both round to the same integer
positions. Exits nonzero on failure.

Caveat: run this in the same data state as the stored backtest (i.e. before
new prices arrive); positions legitimately move with fresh data.

Usage:
    .venv/bin/python analysis/research_harness/g1c_parity_check.py
"""
import sys

CONFIG_FILENAME = "systems.provided.futures_chapter15.futuresconfig.yaml"
STRATEGY_NAME = "paper_classic"
PILOT_INSTRUMENTS = ["CORN", "EUROSTX", "MXP", "SOFR", "US10", "V2X"]
TOLERANCE = 1e-3


def main() -> None:
    from sysdata.data_blob import dataBlob
    from sysobjects.production.tradeable_object import instrumentStrategy
    from sysproduction.data.capital import dataCapital
    from sysproduction.data.optimal_positions import dataOptimalPositions
    from sysproduction.strategy_code.run_system_classic import (
        production_classic_futures_system,
    )

    with dataBlob(log_name="g1c_parity") as data:
        capital = dataCapital(data).get_current_capital_for_strategy(STRATEGY_NAME)
        print(f"recorded strategy capital: {capital:,.2f}")

        optimal = dataOptimalPositions(data)
        stored = {}
        for code in PILOT_INSTRUMENTS:
            position = optimal.get_current_optimal_position_for_instrument_strategy(
                instrumentStrategy(STRATEGY_NAME, code)
            )
            stored[code] = (position.lower_position, position.upper_position)

        system = production_classic_futures_system(
            data,
            CONFIG_FILENAME,
            notional_trading_capital=capital,
            base_currency="USD",
        )
        recomputed = {}
        for code in PILOT_INSTRUMENTS:
            buffers = system.portfolio.get_buffers_for_position(code).ffill()
            recomputed[code] = (
                float(buffers.iloc[-1, 1]),  # bottom
                float(buffers.iloc[-1, 0]),  # top
            )

    print(f"{'':10}{'stored band':>22}{'recomputed band':>22}  verdict")
    all_ok = True
    for code in PILOT_INSTRUMENTS:
        s_lo, s_hi = stored[code]
        r_lo, r_hi = recomputed[code]
        close = abs(s_lo - r_lo) <= TOLERANCE and abs(s_hi - r_hi) <= TOLERANCE
        same_rounded = (round(s_lo), round(s_hi)) == (round(r_lo), round(r_hi))
        ok = close and same_rounded
        all_ok &= ok
        print(
            f"{code:10}{f'[{s_lo:.3f},{s_hi:.3f}]':>22}"
            f"{f'[{r_lo:.3f},{r_hi:.3f}]':>22}  {'OK' if ok else 'DIVERGED'}"
        )

    print(
        f"\nG1c (stored vs recomputed at recorded capital): "
        f"{'PASS' if all_ok else 'FAIL'}"
    )
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
