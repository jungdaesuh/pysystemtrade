"""Shared stack printing for the supervised production scripts."""


def print_stacks(data) -> None:
    from sysproduction.data.orders import dataOrders

    orders = dataOrders(data)
    for name, stack in (
        ("instrument", orders.db_instrument_stack_data),
        ("contract", orders.db_contract_stack_data),
        ("broker", orders.db_broker_stack_data),
    ):
        stack_orders = stack.get_list_of_orders()
        print(f"  {name} stack: {len(stack_orders)} orders")
        for order in stack_orders:
            print(f"    {order}")
