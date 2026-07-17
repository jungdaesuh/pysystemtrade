"""Regression tests for the 2026-07-17 zero-limit-price incident.

IB delayed feeds published bid=0.0 (empty-book sentinel) for V2X; the 'best'
algo priced sell limits from that offside quote and IB rejected five orders
with Error 201 "Message must contain field # 44". Two fixes under test:

1. quote_price_or_nan_if_sentinel — sentinel quotes (<= 0) normalised to nan
   at the IB ticker boundary so isnan validity gates hold everywhere.
2. check_current_limit_price_at_inside_spread — a nan side price returns the
   no-change sentinel instead of nan as the new limit (aggressive path).
"""
import numpy as np

from sysbrokers.IB.ib_futures_contract_price_data import (
    quote_price_or_nan_if_sentinel,
)
from sysexecution.algos.common_functions import (
    check_current_limit_price_at_inside_spread,
    limit_price_is_at_inside_spread,
)


class _StubTicker:
    def __init__(self, side_price: float):
        self.current_side_price = side_price


class _StubOrderWithControls:
    def __init__(self, broker_limit_price: float, side_price: float):
        self._broker_limit_price = broker_limit_price
        self.ticker = _StubTicker(side_price)

    def broker_limit_price(self) -> float:
        return self._broker_limit_price


class TestQuotePriceSentinels:
    def test_zero_bid_is_missing_data(self):
        assert np.isnan(quote_price_or_nan_if_sentinel(0.0))

    def test_ib_minus_one_sentinel_is_missing_data(self):
        assert np.isnan(quote_price_or_nan_if_sentinel(-1.0))

    def test_nan_passes_through_as_nan(self):
        assert np.isnan(quote_price_or_nan_if_sentinel(np.nan))

    def test_genuine_quote_unchanged(self):
        assert quote_price_or_nan_if_sentinel(20.35) == 20.35

    def test_small_genuine_quote_unchanged(self):
        assert quote_price_or_nan_if_sentinel(0.0571) == 0.0571


class TestAggressiveLimitPriceGuard:
    def test_nan_side_price_returns_no_change_sentinel(self):
        order_with_controls = _StubOrderWithControls(
            broker_limit_price=20.35, side_price=np.nan
        )
        result = check_current_limit_price_at_inside_spread(order_with_controls)
        assert result is limit_price_is_at_inside_spread

    def test_limit_already_at_side_price_returns_no_change_sentinel(self):
        order_with_controls = _StubOrderWithControls(
            broker_limit_price=20.3, side_price=20.3
        )
        result = check_current_limit_price_at_inside_spread(order_with_controls)
        assert result is limit_price_is_at_inside_spread

    def test_moved_side_price_returns_new_limit(self):
        order_with_controls = _StubOrderWithControls(
            broker_limit_price=20.35, side_price=20.3
        )
        result = check_current_limit_price_at_inside_spread(order_with_controls)
        assert result == 20.3
