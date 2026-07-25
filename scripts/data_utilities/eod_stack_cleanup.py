"""End-of-day stack cleanup: the production safe_stack_removal, supervised.

Cancels any resting broker orders, books outstanding fills, completes partial
and zero-fill orders, then clears all three stacks — so no state carries into
the next session. Run after the market close of the last venue traded; the
Gateway must be up (port 4002).

Zero-fill completions are normal and expected: an order that never filled is
completed and removed, and tomorrow's backtest regenerates whatever is still
wanted at tomorrow's prices.

Usage:
    .venv/bin/python scripts/data_utilities/eod_stack_cleanup.py
"""
from stack_reporting import print_stacks


def main() -> None:
    from sysdata.data_blob import dataBlob
    from sysexecution.stack_handler.stack_handler import stackHandler

    with dataBlob(log_name="eod_cleanup") as data:
        handler = stackHandler(data)

        print("=== BEFORE ===")
        print_stacks(data)

        handler.safe_stack_removal()

        print("=== AFTER ===")
        print_stacks(data)


if __name__ == "__main__":
    main()
