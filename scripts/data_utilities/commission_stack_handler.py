"""One supervised pass of the stack handler: the commissioning run.

Runs the same methods run_stack_handler schedules, once, in order, with the
state printed between steps so a human can watch the first-ever execution:

  1. check_external_position_break
  2. spawn_children_from_new_instrument_orders  (instrument -> contract orders)
  3. create_broker_orders_from_contract_orders  (contract -> broker orders at IB)
  4. poll loop: process_fills_stack + handle_completed_orders until every
     order is done or --minutes elapses
  5. final state: all three stacks + broker-side positions

Paper account only; the Gateway must be up (port 4002). Position and trade
limits configured via set_paper_limits.py are consulted by the handler.

Usage (during market hours, supervised):
    .venv/bin/python scripts/data_utilities/commission_stack_handler.py --minutes 10
"""
import argparse
import time

from stack_reporting import print_stacks


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--minutes", type=float, default=10.0)
    args = parser.parse_args()

    from sysdata.data_blob import dataBlob
    from sysexecution.stack_handler.stack_handler import stackHandler
    from sysproduction.data.broker import dataBroker

    with dataBlob(log_name="commissioning") as data:
        handler = stackHandler(data)

        print("=== 0 external position break check ===")
        handler.check_external_position_break()

        print("=== 1 spawn contract orders from instrument orders ===")
        handler.spawn_children_from_new_instrument_orders()
        print_stacks(data)

        from sysproduction.data.orders import dataOrders

        order_data = dataOrders(data)
        print(
            f"=== 2+3 create/fill loop (up to {args.minutes:.0f} min, like production) ==="
        )
        deadline = time.time() + args.minutes * 60
        while time.time() < deadline:
            handler.create_broker_orders_from_contract_orders()
            handler.process_fills_stack()
            handler.handle_completed_orders()
            broker_open = order_data.db_broker_stack_data.get_list_of_orders()
            contract_open = order_data.db_contract_stack_data.get_list_of_orders()
            print(
                f"  {time.strftime('%H:%M:%S')} contract orders: {len(contract_open)}, "
                f"broker orders open: {len(broker_open)}"
            )
            if len(broker_open) == 0 and len(contract_open) == 0:
                break
            time.sleep(45)

        print("=== 4 final state ===")
        print_stacks(data)
        broker = dataBroker(data)
        positions = broker.get_all_current_contract_positions()
        print(f"  broker-side contract positions ({len(positions)}):")
        for position in positions:
            print(f"    {position}")


if __name__ == "__main__":
    main()
