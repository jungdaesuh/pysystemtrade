"""Run the daily production price cycle for the stitched pilot instruments.

The full production sequence (run_daily_price_updates) iterates every
instrument in multiple prices; only the gap-stitched pilot six have live
contract chains, so this runs the same production functions scoped to them:

  1. update_fx_prices_for_code       -- FX pairs the pilot needs (EURUSD)
  2. update_active_contracts_for_instrument -- generate/sample the live chain,
                                        refresh expiries from IB
  3. update_historical_prices_for_list_of_instrument_codes -- pull daily bars
                                        for sampled contracts (spike-checked)
  4. update_multiple_adjusted_prices_with_data -- append to multiple/adjusted

Needs the headless Gateway on 4002 (`~/ibc/gatewaystart-headless.sh`) and
PYSYS_PRIVATE_CONFIG_DIR. Safe to run repeatedly; a same-day rerun is a no-op.

Usage:
    .venv/bin/python scripts/data_utilities/daily_cycle_pilot.py
"""
import pandas as pd

PILOT_INSTRUMENTS = ["CORN", "EUROSTX", "MXP", "SOFR", "US10", "V2X"]
FX_CODES = ["EURUSD"]


def main() -> None:
    from sysdata.data_blob import dataBlob
    from sysproduction.data.contracts import dataContracts
    from sysproduction.data.prices import diagPrices
    from sysproduction.update_fx_prices import update_fx_prices_for_code
    from sysproduction.update_historical_prices import (
        update_historical_prices_for_list_of_instrument_codes,
    )
    from sysproduction.update_multiple_adjusted_prices import (
        update_multiple_adjusted_prices_with_data,
    )
    from sysproduction.update_sampled_contracts import (
        update_active_contracts_for_instrument,
    )

    with dataBlob(log_name="daily_cycle_pilot") as data:
        print("=== 1/4 FX ===")
        for fx_code in FX_CODES:
            update_fx_prices_for_code(fx_code, data)

        print("=== 2/4 sampled contracts ===")
        for code in PILOT_INSTRUMENTS:
            update_active_contracts_for_instrument(code, data)

        diag_contracts = dataContracts(data)
        for code in PILOT_INSTRUMENTS:
            sampled = diag_contracts.get_all_sampled_contracts(code)
            print(f"  {code}: sampling {[c.date_str for c in sampled]}")

        print("=== 3/4 historical contract prices ===")
        update_historical_prices_for_list_of_instrument_codes(
            data=data, list_of_instrument_codes=PILOT_INSTRUMENTS
        )

        print("=== 4/4 multiple + adjusted prices ===")
        for code in PILOT_INSTRUMENTS:
            update_multiple_adjusted_prices_with_data(data, instrument_code=code)

        print("\n=== STATUS ===")
        diag = diagPrices(data)
        for code in PILOT_INSTRUMENTS:
            multiple = pd.DataFrame(diag.get_multiple_prices(code))
            adjusted = pd.Series(diag.get_adjusted_prices(code))
            print(
                f"  {code:10} multiple->{multiple.index[-1].date()} "
                f"current={multiple['PRICE_CONTRACT'].iloc[-1]} "
                f"adjusted->{adjusted.index[-1].date()} ({adjusted.iloc[-1]:.4f})"
            )


if __name__ == "__main__":
    main()
