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

Self-healing: IB Gateway exits itself daily at 23:45 ET, so if port 4002 is
down this script relaunches it via `~/ibc/gatewaystart-headless.sh` (IBC does
the full re-login) and waits for the API port before proceeding. Needs
PYSYS_PRIVATE_CONFIG_DIR. Safe to run repeatedly; a same-day rerun is a no-op.

Unattended-run protections:
  * Overlap lock: an exclusive non-blocking flock on ~/ibc/daily_cycle.lock is
    taken at the top of main() and held for the whole run; a concurrent second
    cycle prints "another cycle is running - exiting" and exits 1.
  * Authenticated broker check: once port 4002 is open, ensure_gateway()
    verifies a real API session (ib_async, clientId 993) by requesting and
    printing the IB server time -- an open port alone can lie during Gateway
    startup. One retry after 20s, then exit 1 pointing at
    ~/ibc/logs/ibc-gateway.log.
  * Freshness assertion: after the STATUS report, every pilot instrument's
    multiple-prices last date must be within 3 business days of today
    (numpy busday_count); stale instruments are printed and the run exits 1
    so the cron log records the failure. Friday data on a weekend run is
    0-1 business days back and passes.

Usage:
    .venv/bin/python scripts/data_utilities/daily_cycle_pilot.py
"""
import datetime
import fcntl
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import TextIO

import numpy as np
import pandas as pd
from ib_async import IB

PILOT_INSTRUMENTS = ["CORN", "EUROSTX", "MXP", "SOFR", "US10", "V2X"]
FX_CODES = ["EURUSD"]
GATEWAY_PORT = 4002
GATEWAY_LAUNCHER = Path.home() / "ibc" / "gatewaystart-headless.sh"
GATEWAY_STARTUP_TIMEOUT_S = 180
CYCLE_LOCK_FILE = Path.home() / "ibc" / "daily_cycle.lock"
API_CHECK_CLIENT_ID = 993
API_CHECK_TIMEOUT_S = 15
API_CHECK_RETRY_DELAY_S = 20
MAX_STALE_BUSINESS_DAYS = 3


def port_is_up(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(1)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def acquire_cycle_lock() -> TextIO:
    """Take the exclusive run lock; the returned handle must stay referenced."""
    lock_file = open(CYCLE_LOCK_FILE, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("another cycle is running - exiting")
        sys.exit(1)
    return lock_file


def verify_api_session() -> None:
    """Prove the Gateway accepts an authenticated API session, not just a socket."""
    for attempt in (1, 2):
        ib = IB()
        try:
            ib.connect(
                "127.0.0.1",
                GATEWAY_PORT,
                clientId=API_CHECK_CLIENT_ID,
                timeout=API_CHECK_TIMEOUT_S,
            )
            server_time = ib.reqCurrentTime()
        except Exception as error:
            ib.disconnect()
            if attempt == 1:
                print(
                    f"broker API check failed ({error!r}); "
                    f"retrying in {API_CHECK_RETRY_DELAY_S}s"
                )
                time.sleep(API_CHECK_RETRY_DELAY_S)
                continue
            print(
                f"broker API check failed twice ({error!r}) -- port "
                f"{GATEWAY_PORT} is open but no authenticated API session; "
                "check ~/ibc/logs/ibc-gateway.log"
            )
            sys.exit(1)
        print(f"broker API session OK; IB server time {server_time}")
        ib.disconnect()
        return


def ensure_gateway() -> None:
    if port_is_up(GATEWAY_PORT):
        print(f"gateway already up on {GATEWAY_PORT}")
        verify_api_session()
        return
    print(f"gateway down; launching {GATEWAY_LAUNCHER}")
    subprocess.Popen(
        [str(GATEWAY_LAUNCHER)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    deadline = time.time() + GATEWAY_STARTUP_TIMEOUT_S
    while time.time() < deadline:
        if port_is_up(GATEWAY_PORT):
            time.sleep(5)  # let the API layer finish waking after the socket opens
            print(f"gateway up on {GATEWAY_PORT}")
            verify_api_session()
            return
        time.sleep(3)
    raise SystemExit(
        f"gateway did not open port {GATEWAY_PORT} within "
        f"{GATEWAY_STARTUP_TIMEOUT_S}s -- check ~/ibc/logs/ibc-gateway.log"
    )


def main() -> None:
    cycle_lock = acquire_cycle_lock()  # held (referenced) until the run ends
    ensure_gateway()

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
        last_multiple_dates = {}
        for code in PILOT_INSTRUMENTS:
            multiple = pd.DataFrame(diag.get_multiple_prices(code))
            adjusted = pd.Series(diag.get_adjusted_prices(code))
            last_multiple_dates[code] = multiple.index[-1].date()
            print(
                f"  {code:10} multiple->{multiple.index[-1].date()} "
                f"current={multiple['PRICE_CONTRACT'].iloc[-1]} "
                f"adjusted->{adjusted.index[-1].date()} ({adjusted.iloc[-1]:.4f})"
            )

    print("\n=== FRESHNESS ===")
    today = datetime.date.today()
    days_behind = {
        code: int(np.busday_count(last_date, today))
        for code, last_date in last_multiple_dates.items()
    }
    for code, behind in days_behind.items():
        print(
            f"  {code:10} multiple->{last_multiple_dates[code]} "
            f"({behind} business days behind {today})"
        )
    stale = [
        code for code, behind in days_behind.items() if behind > MAX_STALE_BUSINESS_DAYS
    ]
    if stale:
        print(f"STALE (>{MAX_STALE_BUSINESS_DAYS} business days behind): {stale}")
        sys.exit(1)
    print(
        f"freshness OK: all instruments within {MAX_STALE_BUSINESS_DAYS} business days"
    )


if __name__ == "__main__":
    main()
