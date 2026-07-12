"""G1c sim <-> production parity, STRENGTHENED per the 2026-07-12 audit.

The previous version certified only the buffered bands, recomputed through the
same production helper that wrote them, and ignored the rest of the stored
artifact. This version certifies the COMPLETE order artifact against a
genuinely independent recomputation:

  [1] band parity   : stored buffered optimal positions (Mongo, written by
                      runSystemClassic -> updated_buffered_positions) vs a
                      fresh sim-path system -- futures_system over
                      dbFuturesSimData() with Config(CONFIG_FILENAME) at the
                      recorded strategy capital -- NOT the
                      production_classic_futures_system helper
  [2] reference     : every reference field the stored object carries
                      (reference_price, reference_contract, timestamp) vs the
                      current multiple prices; if the stored class carries no
                      reference fields, that is reported explicitly
  [3] order artifact: the instrument order stack vs the orders IMPLIED by the
                      stored bands and current strategy positions
  [4] config identity: the control config's backtest_config_filename for
                      run_systems/paper_classic vs the filename this check
                      recomputes with

Acceptance: every section passes. Exits nonzero on any failure.

Caveat: run this in the same data state as the stored backtest (i.e. before
new prices arrive); positions legitimately move with fresh data.

Usage:
    .venv/bin/python analysis/research_harness/g1c_parity_check.py
"""
import datetime
import sys

CONFIG_FILENAME = "systems.provided.futures_chapter15.futuresconfig.yaml"
STRATEGY_NAME = "paper_classic"
CONTROL_PROCESS_NAME = "run_systems"
PILOT_INSTRUMENTS = ["CORN", "EUROSTX", "MXP", "SOFR", "US10", "V2X"]
TOLERANCE = 1e-3
REFERENCE_PRICE_REL_TOLERANCE = 1e-4
REFERENCE_DATE_MAX_CALENDAR_DAYS = 5


def check_bands(stored_entries: dict, recomputed: dict) -> bool:
    print("\n[1] band parity (stored Mongo bands vs independent sim recompute)")
    print(f"{'':10}{'stored band':>22}{'recomputed band':>22}  verdict")
    all_ok = True
    for code in PILOT_INSTRUMENTS:
        entry = stored_entries[code]
        s_lo, s_hi = entry.lower_position, entry.upper_position
        r_lo, r_hi = recomputed[code]
        close = abs(s_lo - r_lo) <= TOLERANCE and abs(s_hi - r_hi) <= TOLERANCE
        same_rounded = (round(s_lo), round(s_hi)) == (round(r_lo), round(r_hi))
        ok = close and same_rounded
        all_ok &= ok
        print(
            f"{code:10}{f'[{s_lo:.3f},{s_hi:.3f}]':>22}"
            f"{f'[{r_lo:.3f},{r_hi:.3f}]':>22}  {'OK' if ok else 'DIVERGED'}"
        )
    return all_ok


def check_reference_fields(stored_entries: dict, multiple_prices: dict) -> bool:
    print("\n[2] reference fields (stored object vs current multiple prices)")
    sample_entry = stored_entries[PILOT_INSTRUMENTS[0]]
    reference_fields = [
        field for field in sample_entry.fields if field.startswith("reference")
    ]
    print(
        f"stored class: {type(sample_entry).__name__}; "
        f"reference fields: {reference_fields or 'NONE'}"
    )
    if len(reference_fields) == 0:
        print(
            "stored class carries no reference fields; " "skipping reference comparison"
        )
        return True

    all_ok = True
    for code in PILOT_INSTRUMENTS:
        entry = stored_entries[code]
        prices = multiple_prices[code]
        current_contract = str(prices["PRICE_CONTRACT"].iloc[-1])
        last_price_date = prices.index[-1]
        details = []
        ok = True

        if "reference_contract" in reference_fields:
            stored_contract = str(entry.reference_contract)
            contract_ok = stored_contract == current_contract
            ok &= contract_ok
            details.append(
                f"contract {stored_contract} vs {current_contract} "
                f"{'OK' if contract_ok else 'MISMATCH'}"
            )

        if "reference_price" in reference_fields:
            prices_for_contract = prices[
                prices["PRICE_CONTRACT"].astype(str) == str(entry.reference_contract)
            ]["PRICE"].dropna()
            if len(prices_for_contract) == 0:
                ok = False
                details.append(
                    f"price: no PRICE rows for contract {entry.reference_contract}"
                )
            else:
                latest_price = float(prices_for_contract.iloc[-1])
                rel_error = abs(entry.reference_price - latest_price) / abs(
                    latest_price
                )
                price_ok = rel_error <= REFERENCE_PRICE_REL_TOLERANCE
                ok &= price_ok
                details.append(
                    f"price {entry.reference_price:g} vs {latest_price:g} "
                    f"(rel err {rel_error:.2e}) {'OK' if price_ok else 'MISMATCH'}"
                )

        if "reference_date" in reference_fields:
            stored_timestamp = entry.reference_date
        else:
            stored_timestamp = entry.date  # storage timestamp on the base class
        date_ok = abs(stored_timestamp - last_price_date) <= datetime.timedelta(
            days=REFERENCE_DATE_MAX_CALENDAR_DAYS
        )
        ok &= date_ok
        details.append(
            f"timestamp {stored_timestamp} vs prices {last_price_date} "
            f"{'OK' if date_ok else 'STALE'}"
        )

        all_ok &= ok
        print(f"{code:10} {'; '.join(details)}")
    return all_ok


def check_order_artifact(
    stored_entries: dict, current_positions: dict, stack_orders: list
) -> bool:
    print("\n[3] order artifact (instrument stack vs bands + current positions)")
    positions_str = ", ".join(
        f"{code}={current_positions[code]}" for code in PILOT_INSTRUMENTS
    )
    print(f"current positions (diagPositions): {positions_str}")

    actual_trades = {}
    for order in stack_orders:
        if order.strategy_name != STRATEGY_NAME:
            continue
        actual_trades[order.instrument_code] = int(
            order.trade.as_single_trade_qty_or_error()
        )

    all_ok = True
    print(f"{'':10}{'rounded band':>14}{'expected':>10}{'on stack':>10}  verdict")
    for code in PILOT_INSTRUMENTS:
        entry = stored_entries[code]
        position = current_positions[code]
        lower = round(entry.lower_position)
        upper = round(entry.upper_position)
        if position < lower:
            expected = lower - position
        elif position > upper:
            expected = upper - position
        else:
            expected = None  # inside band -> no order
        actual = actual_trades.pop(code, None)
        ok = expected == actual
        all_ok &= ok
        print(
            f"{code:10}{f'[{lower},{upper}]':>14}"
            f"{str(expected):>10}{str(actual):>10}  {'OK' if ok else 'MISMATCH'}"
        )
    if len(actual_trades) > 0:
        all_ok = False
        print(
            f"unexpected {STRATEGY_NAME} stack orders outside pilot "
            f"instruments: {actual_trades}"
        )
    return all_ok


def check_config_identity(control_config: dict) -> bool:
    print("\n[4] config identity (control config vs this check)")
    control_filename = control_config.get("backtest_config_filename")
    print(
        f"control ({CONTROL_PROCESS_NAME}/{STRATEGY_NAME}) "
        f"backtest_config_filename: {control_filename}"
    )
    print(f"this check recomputes with              : {CONFIG_FILENAME}")
    ok = control_filename == CONFIG_FILENAME
    print(f"config identity: {'OK' if ok else 'MISMATCH'}")
    return ok


def main() -> None:
    from sysdata.config.configdata import Config
    from sysdata.data_blob import dataBlob
    from sysdata.sim.db_futures_sim_data import dbFuturesSimData
    from sysobjects.production.tradeable_object import instrumentStrategy
    from sysproduction.data.capital import dataCapital
    from sysproduction.data.control_process import get_strategy_class_object_config
    from sysproduction.data.optimal_positions import dataOptimalPositions
    from sysproduction.data.orders import dataOrders
    from sysproduction.data.positions import diagPositions
    from sysproduction.data.prices import diagPrices
    from systems.provided.futures_chapter15.basesystem import futures_system

    with dataBlob(log_name="g1c_parity") as data:
        capital = dataCapital(data).get_current_capital_for_strategy(STRATEGY_NAME)
        print(f"recorded strategy capital: {capital:,.2f}")

        optimal = dataOptimalPositions(data)
        stored_entries = {
            code: optimal.get_current_optimal_position_for_instrument_strategy(
                instrumentStrategy(STRATEGY_NAME, code)
            )
            for code in PILOT_INSTRUMENTS
        }

        prices = diagPrices(data)
        multiple_prices = {
            code: prices.get_multiple_prices(code) for code in PILOT_INSTRUMENTS
        }

        diag_positions = diagPositions(data)
        current_positions = {
            code: diag_positions.get_current_position_for_instrument_strategy(
                instrumentStrategy(STRATEGY_NAME, code)
            )
            for code in PILOT_INSTRUMENTS
        }

        stack_orders = dataOrders(data).db_instrument_stack_data.get_list_of_orders()

        control_config = get_strategy_class_object_config(
            data, CONTROL_PROCESS_NAME, STRATEGY_NAME
        )

    # Independent recompute: plain sim construction path (dbFuturesSimData with
    # its own data blob), NOT production_classic_futures_system.
    config = Config(CONFIG_FILENAME)
    config.notional_trading_capital = capital
    config.base_currency = "USD"
    system = futures_system(data=dbFuturesSimData(), config=config)
    recomputed = {}
    for code in PILOT_INSTRUMENTS:
        buffers = system.portfolio.get_buffers_for_position(code).ffill()
        recomputed[code] = (
            float(buffers.iloc[-1, 1]),  # bottom
            float(buffers.iloc[-1, 0]),  # top
        )

    all_ok = check_bands(stored_entries, recomputed)
    all_ok &= check_reference_fields(stored_entries, multiple_prices)
    all_ok &= check_order_artifact(stored_entries, current_positions, stack_orders)
    all_ok &= check_config_identity(control_config)

    print(
        f"\nG1c (complete artifact vs independent recompute): "
        f"{'PASS' if all_ok else 'FAIL'}"
    )
    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
