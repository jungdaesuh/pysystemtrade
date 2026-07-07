"""Smoke test for the IB Gateway connection chain.

Stage 1 (default): bare ib_async connect -> account summary. Proves Gateway API
config, port, and credentials before pysystemtrade is involved.
Stage 2 (--pst): pysystemtrade connectionIB, which exercises private config
resolution (PYSYS_PRIVATE_CONFIG_DIR) and the sysbrokers layer.

Usage (from repo root, paper gateway on 4002):
    .venv/bin/python scripts/ib/smoke_test_ib_connection.py
    .venv/bin/python scripts/ib/smoke_test_ib_connection.py --port 4001   # live gateway
    .venv/bin/python scripts/ib/smoke_test_ib_connection.py --pst

Expected result: your DU... (paper) or U... (live) account id in the summary.
"""
import argparse

SUMMARY_TAGS = ("AccountType", "NetLiquidation", "TotalCashValue", "AvailableFunds")


def bare_ib_async_check(host: str, port: int, client_id: int) -> None:
    from ib_async import IB

    ib = IB()
    ib.connect(host, port, clientId=client_id, timeout=10)
    print(f"connected: {ib.isConnected()} | server time: {ib.reqCurrentTime()}")
    for row in ib.accountSummary():
        if row.tag in SUMMARY_TAGS:
            print(f"{row.account}  {row.tag} = {row.value} {row.currency}")
    ib.disconnect()


def pysystemtrade_check(client_id: int) -> None:
    from sysbrokers.IB.ib_connection import connectionIB

    conn = connectionIB(client_id)
    print(f"pysystemtrade connection: {conn}")
    conn.close_connection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4002, help="4002 paper, 4001 live")
    parser.add_argument("--client-id", type=int, default=999)
    parser.add_argument(
        "--pst",
        action="store_true",
        help="also test pysystemtrade connectionIB (needs private config)",
    )
    args = parser.parse_args()

    bare_ib_async_check(args.host, args.port, args.client_id)
    if args.pst:
        pysystemtrade_check(args.client_id)
