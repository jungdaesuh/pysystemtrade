"""Deploy Phase 1 of the portfolio policy in one reviewed command.

Phase 1 allocation (docs/custom/plans/portfolio_policy.md): SGOV 65% (55% floor
+ 10% engine reserve), VTI 10%, VEA 10%, GLDM 8%, VGIT 7% -- five US-listed ETFs
bought with marketable limit orders (priced off the ask when available; the
last/close fallbacks serve off-hours dry runs and may not be marketable).

Default is a dry run: connect, qualify contracts, price them, size whole-share
quantities (leftover fractional dollars fold into the SGOV line), and print a
whatIfOrder ticket table. No orders are submitted. Pass --live to actually place
orders; this additionally requires typing YES at an interactive confirm.

Usage (paper gateway on 4002):
    .venv/bin/python scripts/ib/deploy_phase1.py --capital 1000000
    .venv/bin/python scripts/ib/deploy_phase1.py --capital 1000000 --live
"""
import argparse
import datetime
import logging
import math
import sys

ALLOCATIONS = {"SGOV": 65.0, "VTI": 10.0, "VEA": 10.0, "GLDM": 8.0, "VGIT": 7.0}


def resolve_price(ticker) -> float:
    for price in (ticker.ask, ticker.last, ticker.close):
        if price and not math.isnan(price) and price > 0:
            return price
    return float("nan")


def size_orders(capital: float, prices: dict) -> dict:
    """Whole shares per ticker, rounded down; rounding leftover folds into SGOV."""
    tickets = {}
    leftover = 0.0
    for ticker, pct in ALLOCATIONS.items():
        if ticker == "SGOV":
            continue
        target = capital * pct / 100
        price = prices[ticker]
        shares = int(target // price) if price > 0 and not math.isnan(price) else 0
        leftover += target - shares * price if shares else 0.0
        tickets[ticker] = (pct, target, price, shares)
    sgov_price = prices["SGOV"]
    sgov_target = capital * ALLOCATIONS["SGOV"] / 100 + leftover
    sgov_shares = (
        int(sgov_target // sgov_price)
        if sgov_price > 0 and not math.isnan(sgov_price)
        else 0
    )
    tickets["SGOV"] = (ALLOCATIONS["SGOV"], sgov_target, sgov_price, sgov_shares)
    return {ticker: tickets[ticker] for ticker in ALLOCATIONS}


def fmt_money(value) -> str:
    if value is None or math.isnan(value):
        return "n/a"
    return f"${value:,.2f}"


def dry_run(ib, contracts: dict, tickets: dict) -> None:
    from ib_async import LimitOrder, OrderState

    header = f"{'TICKER':8}{'ALLOC%':>8}{'TARGET $':>14}{'PRICE':>10}{'SHARES':>8}{'EST COMM':>12}{'EST MARGIN':>14}"
    print(header)
    print("-" * len(header))
    for ticker, (pct, target, price, shares) in tickets.items():
        if shares <= 0:
            print(
                f"{ticker:8}{pct:>8.1f}{fmt_money(target):>14}{fmt_money(price):>10}{'0':>8}{'--':>12}{'--':>14}"
            )
            continue
        # tif must be explicit: a blank tif trips IB order-preset error 10349,
        # which short-circuits whatIfOrder's response before the real OrderState arrives.
        order = LimitOrder("BUY", shares, round(price, 2), tif="DAY")
        state = ib.whatIfOrder(contracts[ticker], order)
        if not isinstance(state, OrderState):
            print(f"{ticker:8} whatIfOrder returned no order state -- got: {state!r}")
            continue
        # margin fields come back from IBKR as raw strings; .numeric() converts
        # them (and resolves the UNSET_DOUBLE sentinel) to float | None.
        state = state.numeric()
        commission = fmt_money(state.commission)
        margin = fmt_money(state.initMarginChange)
        print(
            f"{ticker:8}{pct:>8.1f}{fmt_money(target):>14}{fmt_money(price):>10}{shares:>8}{commission:>12}{margin:>14}"
        )
        if state.warningText:
            print(f"    warning: {state.warningText}")


def place_and_wait(ib, contracts: dict, tickets: dict, timeout_s: float = 60.0) -> dict:
    from ib_async import LimitOrder

    trades = {}
    for ticker, (_, _, price, shares) in tickets.items():
        if shares <= 0:
            continue
        order = LimitOrder("BUY", shares, round(price, 2), tif="DAY")
        trades[ticker] = ib.placeOrder(contracts[ticker], order)

    deadline = datetime.datetime.now() + datetime.timedelta(seconds=timeout_s)
    while datetime.datetime.now() < deadline:
        if all(trade.isDone() for trade in trades.values()):
            break
        ib.waitOnUpdate(timeout=2)
    return trades


def print_decisions_block(trades: dict, account: str) -> None:
    print(
        f"\n### Phase 1 deployment -- {datetime.date.today().isoformat()} (account {account})"
    )
    print("| Ticker | Qty filled | Fill price | $ deployed | Status |")
    print("|---|---|---|---|---|")
    total = 0.0
    for ticker, trade in trades.items():
        status = trade.orderStatus
        deployed = status.filled * status.avgFillPrice
        total += deployed
        print(
            f"| {ticker} | {status.filled:g} | {fmt_money(status.avgFillPrice)} | {fmt_money(deployed)} | {status.status} |"
        )
    print(f"\n**Total deployed:** {fmt_money(total)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--capital", type=float, required=True, help="capital to deploy, USD"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002, help="4002 paper, 4001 live")
    parser.add_argument("--client-id", type=int, default=997)
    parser.add_argument(
        "--live", action="store_true", help="place orders (default: dry run only)"
    )
    parser.add_argument(
        "--allow-live-account",
        action="store_true",
        help="permit a non-DU (real money) account",
    )
    args = parser.parse_args()

    if args.capital <= 0:
        sys.exit("--capital must be positive")
    if not math.isclose(sum(ALLOCATIONS.values()), 100.0):
        sys.exit("ALLOCATIONS must sum to 100")

    logging.getLogger("ib_async").addHandler(logging.StreamHandler())
    logging.getLogger("ib_async").setLevel(logging.INFO)

    from ib_async import IB, Stock

    ib = IB()
    ib.connect(args.host, args.port, clientId=args.client_id, timeout=10)
    try:
        account = ib.managedAccounts()[0]
        if not account.startswith("DU") and not args.allow_live_account:
            sys.exit(
                f"account {account} is not a paper account (DU...); pass --allow-live-account to override"
            )

        contracts = {ticker: Stock(ticker, "SMART", "USD") for ticker in ALLOCATIONS}
        ib.qualifyContracts(*contracts.values())

        ib.reqMarketDataType(3)  # delayed data; falls back further to prior close below
        tickers = ib.reqTickers(*contracts.values())
        prices = {t.contract.symbol: resolve_price(t) for t in tickers}

        tickets = size_orders(args.capital, prices)

        if not args.live:
            dry_run(ib, contracts, tickets)
            return

        confirm = input(
            f"About to place LIVE orders on account {account}. Type YES to continue: "
        )
        if confirm != "YES":
            sys.exit("aborted: confirmation not given")

        trades = place_and_wait(ib, contracts, tickets)
        print_decisions_block(trades, account)
    finally:
        ib.disconnect()


if __name__ == "__main__":
    main()
