"""Stitch the 2024-03 -> present gap in multiple/adjusted futures prices from IB.

The shipped seed data ends 2024-03-28, so every contract chain anchored on the
last multiple-prices row is long expired and production sampling is a no-op
(see docs/custom/learnings/README.md). This script closes the gap using only
IB's free historical daily bars:

  1. Enumerate the held-contract chain from the seed's current contract to the
     present using the instrument's roll parameters.
  2. Fetch daily bars for every chain/carry contract directly via ib_async with
     includeExpired and endDateTime anchored at each contract's EXPIRY (the
     production fetcher anchors at `now` with a 1y duration, which can never
     reach the gap). IB serves expired contracts for ~2 years post-expiry, so
     the earliest gap contracts may be gone; the chain then starts at the first
     fetchable contract and the boundary roll jumps straight to it ("skip
     splice") on the seed's last date -- the differential is still measured on
     one shared date, so adjusted-price continuity is exact; what is
     approximated is WHICH contract the synthetic history holds between the
     boundary and that contract's natural roll-in date.
  3. Validate price scale against the seed's own last row (catches IB price-
     magnifier surprises, e.g. CORN's configured magnifier of 100).
  4. Rebuild multiple prices through the gap. Rolls happen at the last shared
     trading date on or before the roll-parameters' desired_roll_date (expiry +
     RollOffsetDays), mirroring how the seed history rolled; roll rows use
     production's +1-second convention with the pre-roll row's FORWARD carrying
     the incoming contract, so the panama differential is well-defined.
  5. Re-stitch adjusted prices (panama) over the full history and verify that
     pre-gap daily differences are unchanged and the stitched window has no
     holes.

Dry run by default: fetches from IB (read-only) and prints the full plan and
verification per instrument. --write persists after backing up the parquet
files it will overwrite.

Usage (paper gateway on 4002, PYSYS_PRIVATE_CONFIG_DIR set):
    .venv/bin/python scripts/data_utilities/gap_stitch.py --instruments CORN
    .venv/bin/python scripts/data_utilities/gap_stitch.py --write
"""
import argparse
import datetime
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

PILOT_INSTRUMENTS = ["CORN", "EUROSTX", "MXP", "SOFR", "US10", "V2X"]
IB_CONFIG_CSV = Path("sysbrokers/IB/config/ib_config_futures.csv")
PACE_SECONDS = 2.0
MAX_STALE_BDAYS = 5
MAX_GAP_CALENDAR_DAYS = 9
MAX_HOLE_BRIDGE_DAYS = 70
SCALE_TOLERANCE = 0.02
COLUMNS = [
    "PRICE",
    "CARRY",
    "FORWARD",
    "PRICE_CONTRACT",
    "CARRY_CONTRACT",
    "FORWARD_CONTRACT",
]


def enumerate_held_chain(start_contract_id: str, roll_parameters, today) -> list:
    """Held-cycle contractDateWithRollParameters from the seed's current contract
    to one beyond today's holding."""
    from sysobjects.contract_dates_and_expiries import contractDate
    from sysobjects.rolls import contractDateWithRollParameters

    chain = []
    current = contractDateWithRollParameters(
        contractDate(start_contract_id), roll_parameters
    )
    while current.desired_roll_date.date() <= today:
        chain.append(current)
        current = current.next_held_contract()
    chain.append(current)  # currently held contract
    chain.append(current.next_held_contract())  # its forward
    return chain


class ibDailyBarFetcher:
    """Daily final prices per contract, expiry-anchored so expired contracts
    inside IB's ~2y window return their real history."""

    def __init__(self, ib, config_row: pd.Series):
        self.ib = ib
        self.config = config_row

    def fetch(self, contract_id: str, today) -> pd.Series:
        # Some products are dual-listed under two IB symbols (CME peso: legacy
        # "MXP" holds the expired history, "6M" only recent contracts), and the
        # config's IBSymbol may be a local-symbol root that can't resolve
        # expired contracts at all. Fetch under both the config symbol and the
        # instrument code and keep the longest series.
        candidates = dict.fromkeys([str(self.config["IBSymbol"]), str(self.config.name)])
        best = pd.Series(dtype=float)
        for symbol in candidates:
            series = self._fetch_for_symbol(symbol, contract_id, today)
            if len(series) > len(best):
                best = series
        return best

    def _fetch_for_symbol(self, symbol: str, contract_id: str, today) -> pd.Series:
        from ib_async import Future

        pattern = Future(
            symbol=symbol,
            lastTradeDateOrContractMonth=contract_id[:6],
            exchange=self.config["IBExchange"],
        )
        if str(self.config["IBCurrency"]) not in ("NA", "nan"):
            pattern.currency = str(self.config["IBCurrency"])
        pattern.includeExpired = True
        details = self.ib.reqContractDetails(pattern)
        time.sleep(PACE_SECONDS / 2)
        if not details:
            return pd.Series(dtype=float)
        qualified = details[0].contract
        qualified.includeExpired = True

        expiry = datetime.datetime.strptime(
            qualified.lastTradeDateOrContractMonth[:8], "%Y%m%d"
        ).date()
        end = (
            ""
            if expiry >= today
            else datetime.datetime.combine(
                expiry + datetime.timedelta(days=1), datetime.time(0, 0)
            )
        )
        bars = []
        # alive contracts anchor at `now`, so reaching the 2024-03 boundary
        # needs a 3y duration; expired ones fall through the ladder as IB allows
        for duration, what in (
            ("3 Y", "TRADES"),
            ("2 Y", "TRADES"),
            ("1 Y", "TRADES"),
            ("1 Y", "MIDPOINT"),
        ):
            try:
                bars = self.ib.reqHistoricalData(
                    qualified,
                    endDateTime=end,
                    durationStr=duration,
                    barSizeSetting="1 day",
                    whatToShow=what,
                    useRTH=True,
                    formatDate=1,
                )
            except Exception:
                bars = []
            time.sleep(PACE_SECONDS)
            if bars:
                if what != "TRADES" or duration == "1 Y":
                    print(f"      ({contract_id}: fell back to {duration}/{what})")
                break
        if not bars:
            return pd.Series(dtype=float)
        series = pd.Series(
            [bar.close for bar in bars],
            index=pd.DatetimeIndex([pd.Timestamp(bar.date) for bar in bars]),
        )
        return series[~series.index.duplicated(keep="last")].sort_index()


def value_at(series: pd.Series, when, max_stale_bdays: int = MAX_STALE_BDAYS) -> float:
    """Last price at or before `when`; NaN if none or staler than the tolerance."""
    if len(series) == 0 or series.index[0] > when:
        return np.nan
    value = series.asof(when)
    last_date = series.index[series.index <= when][-1]
    if np.busday_count(last_date.date(), when.date()) > max_stale_bdays:
        return np.nan
    return float(value)


def determine_scale_factor(
    seed_last_row: pd.Series, seed_last_date, prices: dict, price_magnifier: float
) -> float:
    """Ratio to apply to IB prices so they match the seed's scale, validated on
    a contract the seed itself priced on its last date. Raises if no overlap
    or no candidate factor fits."""
    for column, contract_column in (
        ("PRICE", "PRICE_CONTRACT"),
        ("FORWARD", "FORWARD_CONTRACT"),
        ("CARRY", "CARRY_CONTRACT"),
    ):
        contract_id = str(seed_last_row[contract_column])
        seed_price = float(seed_last_row[column])
        fetched = prices.get(contract_id, pd.Series(dtype=float))
        ib_price = value_at(fetched, seed_last_date)
        if np.isnan(ib_price) or np.isnan(seed_price) or ib_price == 0:
            continue
        for factor in (1.0, price_magnifier, 1.0 / price_magnifier):
            if abs(ib_price * factor / seed_price - 1) < SCALE_TOLERANCE:
                print(
                    f"  scale check vs seed {contract_id} on {seed_last_date.date()}: "
                    f"ib={ib_price:.4f} seed={seed_price:.4f} -> factor {factor:g}"
                )
                return factor
        raise ValueError(
            f"price scale mismatch: IB {contract_id}={ib_price} vs seed "
            f"{seed_price}; no factor in (1, {price_magnifier:g}, "
            f"{1 / price_magnifier:g}) fits"
        )
    raise ValueError(
        "no fetched contract overlaps the seed's last row - cannot validate price scale"
    )


def build_gap_segment(
    seed_last_row: pd.Series,
    seed_last_date,
    chain_ids: list,
    carry_ids: dict,
    forward_after: dict,
    desired_roll_dates: dict,
    prices: dict,
    today,
) -> tuple:
    """Multiple-prices rows from the seed boundary to the present.

    Returns (segment DataFrame, id of the contract held at the end): rolls
    happen only for contracts whose desired_roll_date has already passed; the
    first contract whose roll belongs to the future stays the current holding.
    """
    rows = {}

    def add_row(when, price, price_id, fwd, fwd_id, carry, carry_id):
        rows[when] = {
            "PRICE": price,
            "PRICE_CONTRACT": price_id,
            "FORWARD": fwd,
            "FORWARD_CONTRACT": fwd_id,
            "CARRY": carry,
            "CARRY_CONTRACT": carry_id,
        }

    one_sec = pd.Timedelta(seconds=1)
    prev_roll = seed_last_date
    holder = chain_ids[0]
    holes = []

    for i in range(len(chain_ids) - 1):
        outgoing, incoming = chain_ids[i], chain_ids[i + 1]
        outgoing_prices = prices.get(outgoing, pd.Series(dtype=float))
        incoming_prices = prices[incoming]

        if len(outgoing_prices) > 0 and desired_roll_dates[outgoing].date() > today:
            break  # this contract is still held today; no further rolls

        if len(outgoing_prices) == 0:
            # Skip splice: outgoing exists only in the seed (aged out of IB's
            # window). Roll ON the seed's last date; the pre-roll row supplies
            # FORWARD=incoming so the differential is on one shared date.
            if i != 0:
                raise ValueError(f"unfetchable contract {outgoing} mid-chain")
            incoming_at_roll = value_at(incoming_prices, seed_last_date)
            if np.isnan(incoming_at_roll):
                raise ValueError(
                    f"boundary roll impossible: {incoming} has no price at/near "
                    f"{seed_last_date.date()}"
                )
            add_row(
                seed_last_date + one_sec,
                float(seed_last_row["PRICE"]),
                outgoing,
                incoming_at_roll,
                incoming,
                seed_last_row["CARRY"],
                seed_last_row["CARRY_CONTRACT"],
            )
            roll_date = seed_last_date
            roll_row_time = seed_last_date + 2 * one_sec
        else:
            shared = outgoing_prices.index.intersection(incoming_prices.index)
            shared = shared[shared > prev_roll]
            carry_series = prices.get(carry_ids[outgoing], pd.Series(dtype=float))
            if len(shared) == 0:
                # Hole bridge: IB has no data for EITHER contract between the
                # outgoing's last bar and the incoming's first (e.g. the CME FX
                # symbology migration hole, 2025-03..05). Returns are flat
                # across the hole; the price jump is absorbed into the roll
                # differential, so continuity is preserved but the hole window
                # carries no information. Bounded and loudly reported.
                hole_start = outgoing_prices.index[-1]
                hole_end = incoming_prices.index[0]
                hole_days = (hole_end - hole_start).days
                if hole_end <= prev_roll or hole_days <= 0 or hole_days > MAX_HOLE_BRIDGE_DAYS:
                    raise ValueError(
                        f"cannot bridge {outgoing} -> {incoming}: "
                        f"{hole_days}d hole exceeds {MAX_HOLE_BRIDGE_DAYS}d cap"
                    )
                print(
                    f"  WARNING: bridging {hole_days}-day IB data hole "
                    f"{hole_start.date()}..{hole_end.date()} at roll "
                    f"{outgoing} -> {incoming} (returns flat across it)"
                )
                holes.append((outgoing, incoming, hole_start, hole_end))
                for when in outgoing_prices.index[
                    (outgoing_prices.index > prev_roll)
                    & (outgoing_prices.index <= hole_start)
                ]:
                    add_row(
                        when,
                        float(outgoing_prices[when]),
                        outgoing,
                        value_at(incoming_prices, when),
                        incoming,
                        value_at(carry_series, when),
                        carry_ids[outgoing],
                    )
                add_row(
                    hole_end,
                    float(outgoing_prices[hole_start]),
                    outgoing,
                    float(incoming_prices[hole_end]),
                    incoming,
                    value_at(carry_series, hole_end),
                    carry_ids[outgoing],
                )
                roll_date = hole_end
                roll_row_time = hole_end + one_sec
            else:
                at_or_before_desired = shared[shared <= desired_roll_dates[outgoing]]
                roll_date = (
                    at_or_before_desired[-1] if len(at_or_before_desired) else shared[0]
                )
                period_dates = outgoing_prices.index[
                    (outgoing_prices.index > prev_roll)
                    & (outgoing_prices.index <= roll_date)
                ]
                for when in period_dates:
                    add_row(
                        when,
                        float(outgoing_prices[when]),
                        outgoing,
                        value_at(incoming_prices, when),
                        incoming,
                        value_at(carry_series, when),
                        carry_ids[outgoing],
                    )
                roll_row_time = roll_date + one_sec

        # roll row: incoming becomes the price contract at the same instant
        next_id = forward_after[incoming]
        incoming_carry = prices.get(carry_ids.get(incoming, ""), pd.Series(dtype=float))
        add_row(
            roll_row_time,
            float(value_at(incoming_prices, roll_date)),
            incoming,
            value_at(prices.get(next_id, pd.Series(dtype=float)), roll_date),
            next_id,
            value_at(incoming_carry, roll_date),
            carry_ids.get(incoming, ""),
        )
        prev_roll = roll_date
        holder = incoming

    # final period: the contract held today carries through to the present
    holder_pos = chain_ids.index(holder)
    next_id = (
        chain_ids[holder_pos + 1]
        if holder_pos + 1 < len(chain_ids)
        else forward_after[holder]
    )
    holder_prices = prices[holder]
    next_series = prices.get(next_id, pd.Series(dtype=float))
    carry_series = prices.get(carry_ids.get(holder, ""), pd.Series(dtype=float))
    for when in holder_prices.index[holder_prices.index > prev_roll]:
        add_row(
            when,
            float(holder_prices[when]),
            holder,
            value_at(next_series, when),
            next_id,
            value_at(carry_series, when),
            carry_ids.get(holder, ""),
        )

    segment = pd.DataFrame.from_dict(rows, orient="index")
    return segment[COLUMNS].sort_index(), holder, holes


def stitch_instrument(data, ib, ib_config: pd.DataFrame, instrument_code: str, today):
    from sysdata.csv.csv_roll_parameters import csvRollParametersData
    from sysobjects.adjusted_prices import futuresAdjustedPrices
    from sysobjects.multiple_prices import futuresMultiplePrices
    from sysproduction.data.prices import diagPrices

    diag = diagPrices(data)
    seed_mp = pd.DataFrame(diag.get_multiple_prices(instrument_code))
    seed_last_date = seed_mp.index[-1]
    seed_last_row = seed_mp.iloc[-1]
    start_id = str(seed_last_row["PRICE_CONTRACT"])
    print(
        f"  seed ends {seed_last_date.date()}; current={start_id} "
        f"forward={seed_last_row['FORWARD_CONTRACT']} carry={seed_last_row['CARRY_CONTRACT']}"
    )

    roll_parameters = csvRollParametersData().get_roll_parameters(instrument_code)
    chain_with_rolls = enumerate_held_chain(start_id, roll_parameters, today)
    held_ids = [c.date_str for c in chain_with_rolls]
    carry_ids = {c.date_str: c.carry_contract().date_str for c in chain_with_rolls}
    forward_after = {
        c.date_str: c.next_held_contract().date_str for c in chain_with_rolls
    }
    desired_roll_dates = {c.date_str: c.desired_roll_date for c in chain_with_rolls}
    fetch_ids = sorted(
        set(held_ids)
        | {carry_ids[h] for h in held_ids}
        | {forward_after[held_ids[-1]]}
        | {str(seed_last_row["FORWARD_CONTRACT"]), str(seed_last_row["CARRY_CONTRACT"])}
    )
    print(f"  held chain ({len(held_ids)}): {' '.join(held_ids)}")
    print(f"  fetching {len(fetch_ids)} contracts from IB")

    fetcher = ibDailyBarFetcher(ib, ib_config.loc[instrument_code])
    prices = {}
    for contract_id in fetch_ids:
        series = fetcher.fetch(contract_id, today)
        prices[contract_id] = series
        status = (
            f"{series.index[0].date()}..{series.index[-1].date()} ({len(series)} rows)"
            if len(series)
            else "EMPTY (outside IB window?)"
        )
        print(f"    {contract_id}: {status}")

    price_magnifier = float(ib_config.loc[instrument_code, "priceMagnifier"])
    scale = determine_scale_factor(
        seed_last_row, seed_last_date, prices, price_magnifier
    )
    if scale != 1.0:
        prices = {cid: series * scale for cid, series in prices.items()}

    fetchable_held = [h for h in held_ids[1:] if len(prices[h]) > 0]
    skipped = [h for h in held_ids[1:] if len(prices[h]) == 0]
    if not fetchable_held:
        raise ValueError("no held contract in the chain is fetchable from IB")
    chain_ids = [held_ids[0]] + fetchable_held

    segment, holder, holes = build_gap_segment(
        seed_last_row,
        seed_last_date,
        chain_ids,
        carry_ids,
        forward_after,
        desired_roll_dates,
        prices,
        today,
    )
    new_mp_df = pd.concat([seed_mp, segment]).sort_index()
    new_mp = futuresMultiplePrices(new_mp_df)
    new_adjusted = futuresAdjustedPrices.stitch_multiple_prices(
        new_mp, forward_fill=True
    )

    # verification 1: pre-gap daily differences must be preserved exactly
    old_adjusted = pd.Series(diag.get_adjusted_prices(instrument_code))
    old_diffs = old_adjusted.diff().dropna()
    new_diffs = new_adjusted.reindex(old_adjusted.index).diff().dropna()
    diffs_match = np.allclose(
        old_diffs.values, new_diffs.reindex(old_diffs.index).values, equal_nan=True
    )
    # verification 2: stitched window continuity
    stitched_index = new_adjusted.index[new_adjusted.index > seed_last_date]
    gaps = (
        np.diff(stitched_index.normalize().unique().values)
        .astype("timedelta64[D]")
        .astype(int)
    )
    max_gap_days = int(gaps.max()) if len(gaps) else 0

    result = dict(
        instrument=instrument_code,
        chain=chain_ids,
        skipped_unfetchable=skipped,
        holes_bridged=holes,
        rows_appended=len(segment),
        last_date=new_mp_df.index[-1],
        current_contract=holder,
        pre_gap_returns_preserved=diffs_match,
        max_calendar_gap_days=max_gap_days,
        new_multiple_prices=new_mp,
        new_adjusted=new_adjusted,
    )
    print(
        f"  built: +{len(segment)} rows to {new_mp_df.index[-1].date()}, "
        f"current={holder}, skipped={skipped or 'none'}, "
        f"pre-gap returns preserved={diffs_match}, max gap {max_gap_days}d"
    )
    if not diffs_match:
        raise ValueError("pre-gap adjusted returns CHANGED - refusing this stitch")
    if max_gap_days > MAX_GAP_CALENDAR_DAYS:
        print(f"  WARNING: {max_gap_days} calendar-day hole inside the stitched window")
    return result


def backup_parquet(parquet_store: Path, instruments: list) -> Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path.home() / "pysystemtrade-backups" / f"gap_stitch_{stamp}"
    for kind in ("futures_multiple_prices", "futures_adjusted_prices"):
        for code in instruments:
            source = parquet_store / kind / f"{code}.parquet"
            if source.exists():
                target = backup_dir / kind
                target.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target / source.name)
    return backup_dir


def persist(data, result: dict) -> None:
    from sysobjects.contracts import futuresContract
    from sysproduction.data.prices import updatePrices

    update = updatePrices(data)
    code = result["instrument"]
    for contract_id in result["chain"][1:]:
        if not data.db_futures_contract.is_contract_in_data(code, contract_id):
            data.db_futures_contract.add_contract_data(
                futuresContract(code, contract_id)
            )
    update.add_multiple_prices(
        code, result["new_multiple_prices"], ignore_duplication=True
    )
    update.add_adjusted_prices(code, result["new_adjusted"], ignore_duplication=True)
    print(f"  WRITTEN: multiple+adjusted prices and contract objects for {code}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--instruments", nargs="+", default=PILOT_INSTRUMENTS)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002)
    parser.add_argument("--client-id", type=int, default=996)
    parser.add_argument(
        "--write", action="store_true", help="persist (default: dry run, no writes)"
    )
    args = parser.parse_args()

    from ib_async import IB

    from sysdata.config.production_config import get_production_config
    from sysdata.data_blob import dataBlob

    ib_config = pd.read_csv(IB_CONFIG_CSV, index_col="Instrument")
    today = datetime.date.today()
    results, failures = [], []

    ib = IB()
    ib.connect(args.host, args.port, clientId=args.client_id, timeout=15)
    try:
        with dataBlob(log_name="gap_stitch") as data:
            if args.write:
                parquet_store = Path(
                    get_production_config().get_element("parquet_store")
                ).expanduser()
                backup_dir = backup_parquet(parquet_store, args.instruments)
                print(f"parquet backup at {backup_dir}")

            for code in args.instruments:
                print(f"\n=== {code} ===")
                try:
                    result = stitch_instrument(data, ib, ib_config, code, today)
                except Exception as exc:
                    print(f"  FAILED: {exc}")
                    failures.append((code, str(exc)))
                    continue
                results.append(result)
                if args.write:
                    persist(data, result)
    finally:
        ib.disconnect()

    print("\n=== SUMMARY ===")
    for result in results:
        holes_note = (
            f", {len(result['holes_bridged'])} hole(s) bridged"
            if result["holes_bridged"]
            else ""
        )
        print(
            f"{result['instrument']:10} stitched to {result['last_date'].date()} "
            f"current={result['current_contract']} "
            f"(+{result['rows_appended']} rows, skipped "
            f"{len(result['skipped_unfetchable'])}{holes_note})"
        )
    for code, error in failures:
        print(f"{code:10} FAILED: {error}")
    if not args.write:
        print("\nDRY RUN - nothing written. Re-run with --write to persist.")


if __name__ == "__main__":
    main()
