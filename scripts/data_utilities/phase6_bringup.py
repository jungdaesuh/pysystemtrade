"""Phase 6 bring-up: capital -> nightly backtest -> optimal positions -> orders.

One-shot initialisation of the paper strategy loop for the pilot six, using
the same production classes the scheduled processes run:

  1. Seed total capital from the paper broker account value (first run only)
  2. Allocate strategy capital per strategy_capital_allocation (100% paper_classic)
  3. Run the production backtest (runSystemClassic.run_backtest) -- writes
     buffered optimal positions to Mongo and pickles the backtest state
  4. Generate instrument orders from optimal-vs-actual positions
     (orderGeneratorForBufferedPositions.get_and_place_orders)
  5. Print optimal positions and the instrument order stack

Needs the headless Gateway (self-heals via daily_cycle_pilot.ensure_gateway)
and the strategy wiring in private_config.yaml (added 2026-07-11).

Usage:
    .venv/bin/python scripts/data_utilities/phase6_bringup.py
"""
STRATEGY_NAME = "paper_classic"
BACKTEST_CONFIG = "systems.provided.futures_chapter15.futuresconfig.yaml"


def main() -> None:
    from daily_cycle_pilot import ensure_gateway

    ensure_gateway()

    from sysdata.data_blob import dataBlob
    from syscore.exceptions import missingData
    from sysexecution.strategies.classic_buffered_positions import (
        orderGeneratorForBufferedPositions,
    )
    from sysproduction.data.broker import dataBroker
    from sysproduction.data.capital import dataCapital
    from sysproduction.data.optimal_positions import dataOptimalPositions
    from sysproduction.data.orders import dataOrders
    from sysproduction.strategy_code.run_system_classic import runSystemClassic
    from sysproduction.update_strategy_capital import updateStrategyCapital

    with dataBlob(log_name="phase6_bringup") as data:
        print("=== 1/5 total capital ===")
        capital = dataCapital(data)
        try:
            total = capital.get_current_total_capital()
            print(f"  total capital already set: {total:,.0f}")
        except missingData:
            broker_value = dataBroker(data).get_total_capital_value_in_base_currency()
            capital.create_initial_capital(
                broker_account_value=broker_value,
                total_capital=broker_value,
                are_you_really_sure=True,
            )
            print(f"  initial capital created from broker value: {broker_value:,.0f}")

        print("=== 2/5 strategy capital allocation ===")
        updateStrategyCapital(data).strategy_allocation()
        strategy_capital = capital.get_current_capital_for_strategy(STRATEGY_NAME)
        print(f"  {STRATEGY_NAME}: {strategy_capital:,.0f}")

        print("=== 3/5 production backtest ===")
        runner = runSystemClassic(
            data, STRATEGY_NAME, backtest_config_filename=BACKTEST_CONFIG
        )
        runner.run_backtest()
        print("  backtest complete; buffered optimal positions written")

        print("=== 4/5 order generation ===")
        generator = orderGeneratorForBufferedPositions(data, STRATEGY_NAME)
        generator.get_and_place_orders()

        print("=== 5/5 state ===")
        from sysobjects.production.tradeable_object import instrumentStrategy

        optimal = dataOptimalPositions(data)
        for code in optimal.get_list_of_instruments_for_strategy_with_optimal_position(
            STRATEGY_NAME
        ):
            position = optimal.get_current_optimal_position_for_instrument_strategy(
                instrumentStrategy(STRATEGY_NAME, code)
            )
            print(f"  optimal {code}: {position}")
        order_data = dataOrders(data)
        instrument_orders = order_data.db_instrument_stack_data.get_list_of_orders()
        print(f"  instrument orders on stack: {len(instrument_orders)}")
        for order in instrument_orders:
            print(f"    {order}")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent))
    main()
