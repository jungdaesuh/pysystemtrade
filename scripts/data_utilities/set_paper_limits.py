"""Configure paper trade and position limits for the pilot strategy.

Turns the policy's kill criteria from prose into enforced controls: hard
per-instrument position caps and one-day trade caps, sized at roughly 2x the
current optimal positions from the $1M paper backtest (a breach therefore
means the system is doing something the backtest never asked for).

Idempotent: re-running overwrites the same limits. Stored in Mongo; the stack
handler and order generators consult them before placing anything.

Usage:
    .venv/bin/python scripts/data_utilities/set_paper_limits.py
"""
# position cap, one-day trade cap -- ~2x the 2026-07-11 optimal positions
LIMITS = {
    "CORN": (65, 65),
    "EUROSTX": (12, 12),
    "MXP": (6, 6),
    "SOFR": (12, 12),
    "US10": (6, 6),
    "V2X": (140, 140),
}
TRADE_LIMIT_PERIOD_DAYS = 1


def main() -> None:
    from sysdata.data_blob import dataBlob
    from sysproduction.data.controls import dataPositionLimits, dataTradeLimits

    with dataBlob(log_name="set_paper_limits") as data:
        position_limits = dataPositionLimits(data)
        trade_limits = dataTradeLimits(data)
        for code, (position_cap, trade_cap) in LIMITS.items():
            position_limits.set_abs_position_limit_for_instrument(code, position_cap)
            trade_limits.update_instrument_limit_with_new_limit(
                code, TRADE_LIMIT_PERIOD_DAYS, trade_cap
            )
            print(
                f"  {code:10} position cap +/-{position_cap:4}   "
                f"trade cap {trade_cap}/day"
            )
    print("limits written to Mongo (consulted by order generation and stack handler)")


if __name__ == "__main__":
    main()
