"""Cold-start shim: create contract-DB objects for the key contracts referenced
by the (seeded) multiple prices, so sysproduction sampling checks can run.

Needed exactly once per instrument after seeding a fresh database from repo
CSVs: `update_sampled_contracts` builds today's contract chain, but
`check_key_contracts_have_not_expired` looks up the price/forward/carry
contracts named in the LAST multiple-prices row — which, on a cold start from
stale CSVs, predate the chain and don't exist in Mongo. This script creates
them (with approximate expiries derived from the contract date), after which
the check correctly reports "YOU NEED TO ROLL" instead of crashing.

Usage:
    .venv/bin/python scripts/data_utilities/bootstrap_key_contracts_from_multiple_prices.py CORN SOFR ...
"""
import sys

from sysdata.data_blob import dataBlob
from sysobjects.contracts import futuresContract
from sysproduction.data.prices import diagPrices


def bootstrap_instrument(data: dataBlob, instrument_code: str) -> list:
    diag_prices = diagPrices(data)
    multiple_prices = diag_prices.get_multiple_prices(instrument_code)
    final_row = multiple_prices.iloc[-1]
    contract_ids = {
        str(final_row[col])
        for col in ("PRICE_CONTRACT", "FORWARD_CONTRACT", "CARRY_CONTRACT")
    }
    created = []
    for contract_id in sorted(contract_ids):
        if not data.db_futures_contract.is_contract_in_data(instrument_code, contract_id):
            contract = futuresContract(instrument_code, contract_id)
            data.db_futures_contract.add_contract_data(contract)
            created.append(contract_id)
    return created


if __name__ == "__main__":
    codes = sys.argv[1:]
    if not codes:
        sys.exit("usage: bootstrap_key_contracts_from_multiple_prices.py CODE [CODE ...]")
    with dataBlob(log_name="bootstrap-key-contracts") as data:
        for code in codes:
            created = bootstrap_instrument(data, code)
            print(f"{code}: created {created or 'nothing (already present)'}")
