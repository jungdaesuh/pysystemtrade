"""Operator approval of spike-quarantined contract prices.

The price-update cycle refuses to write a contract whose new prices trip the
spike check, and keeps refusing every night until a human accepts them. A
contract whose stored series is EMPTY trips it permanently, silently starving
the multiple/adjusted prices downstream (see docs/custom/learnings 2026-07-20).

This is the non-interactive equivalent of accepting the prices in
interactive_manual_check_historical_prices: it re-fetches the broker's cleaned
prices and writes them with the spike check bypassed, then rewrites the merged
series. VERIFY FIRST — compare the stored and broker prices and satisfy
yourself the move is real market behaviour, not bad data. Approving unverified
prices writes bad data into the system of record.

Usage:
    .venv/bin/python scripts/data_utilities/approve_contract_spike.py V2X 20260700 20260800
"""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("instrument_code")
    parser.add_argument("contract_dates", nargs="+")
    args = parser.parse_args()

    from syscore.dateutils import DAILY_PRICE_FREQ
    from sysdata.data_blob import dataBlob
    from sysdata.tools.cleaner import get_config_for_price_filtering
    from sysobjects.contracts import futuresContract
    from sysproduction.data.broker import dataBroker
    from sysproduction.data.prices import diagPrices, updatePrices
    from sysproduction.update_historical_prices import write_merged_prices_for_contract

    with dataBlob(log_name="spike_approval") as data:
        cleaning_config = get_config_for_price_filtering(data)
        diag_prices = diagPrices(data)
        update_prices = updatePrices(data)
        broker = dataBroker(data)

        intraday_frequency = (
            diag_prices.get_intraday_frequency_for_historical_download()
        )
        frequencies = [intraday_frequency, DAILY_PRICE_FREQ]

        for contract_date in args.contract_dates:
            contract = futuresContract(args.instrument_code, contract_date)
            for frequency in frequencies:
                broker_prices = (
                    broker.get_cleaned_prices_at_frequency_for_contract_object(
                        contract, frequency, cleaning_config=cleaning_config
                    )
                )
                rows_added = update_prices.update_prices_at_frequency_for_contract(
                    contract, frequency, broker_prices, check_for_spike=False
                )
                print(f"{contract}: {frequency} +{rows_added} rows")

            write_merged_prices_for_contract(
                data, contract_object=contract, list_of_frequencies=frequencies
            )
            print(f"{contract}: merged prices written")


if __name__ == "__main__":
    main()
