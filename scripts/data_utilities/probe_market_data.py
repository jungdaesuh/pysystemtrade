"""Probe whether the broker serves live top-of-book for each instrument.

Answers one operational question: is the market-data subscription active for
these instruments? A valid bid AND ask inside the wait window means the feed
is live; missingData means it is not (IB logs "Error 354 ... not subscribed"
alongside, and delayed feeds publish no depth, which starves the execution
algo — see docs/custom/learnings).

Contracts are resolved through the system's own priced-contract mapping, so
this keeps working across rolls with no hardcoded contract ids.

Run it during the instrument's TRADING HOURS. A closed market publishes no
quotes either, so a weekend or overnight run reports NO LIVE DATA for every
instrument and tells you nothing about the subscription.

Usage:
    .venv/bin/python scripts/data_utilities/probe_market_data.py CORN US10 MXP SOFR
"""
import argparse

DEFAULT_WAIT_SECONDS = 10


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("instruments", nargs="+")
    parser.add_argument("--wait", type=float, default=DEFAULT_WAIT_SECONDS)
    args = parser.parse_args()

    from syscore.exceptions import missingData
    from sysdata.data_blob import dataBlob
    from sysobjects.contracts import futuresContract
    from sysproduction.data.broker import dataBroker
    from sysproduction.data.contracts import dataContracts

    with dataBlob(log_name="probe_market_data") as data:
        broker = dataBroker(data)
        contracts = dataContracts(data)

        for instrument_code in args.instruments:
            contract_date = contracts.get_priced_contract_id(instrument_code)
            contract = futuresContract(instrument_code, contract_date)
            ticker = broker.get_ticker_object_for_contract(contract)
            try:
                tick = ticker.wait_for_valid_bid_and_ask_and_return_current_tick(
                    wait_time_seconds=args.wait
                )
                print(
                    f"{instrument_code}/{contract_date}: LIVE "
                    f"bid {tick.bid_price} x {tick.bid_size} / "
                    f"ask {tick.ask_price} x {tick.ask_size}"
                )
            except missingData:
                print(f"{instrument_code}/{contract_date}: NO LIVE DATA")
            broker.cancel_market_data_for_contract(contract)


if __name__ == "__main__":
    main()
