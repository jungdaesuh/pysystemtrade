import numpy as np
import pandas as pd

from syscore.dateutils import BUSINESS_DAYS_IN_YEAR
from syscore.pandas.frequency import resample_prices_to_business_day_index


def robust_daily_vol_given_price(price: pd.Series, **kwargs):
    price = resample_prices_to_business_day_index(price)
    daily_returns = price.diff()

    vol = robust_vol_calc(daily_returns, **kwargs)

    return vol


def robust_vol_calc(
    daily_returns: pd.Series,
    days: int = 35,
    min_periods: int = 10,
    vol_abs_min: float = 0.0000000001,
    vol_floor: bool = True,
    floor_min_quant: float = 0.05,
    floor_min_periods: int = 100,
    floor_days: int = 500,
    backfill: bool = False,
    **ignored_kwargs,
) -> pd.Series:
    """
    Robust exponential volatility calculation, assuming daily series of prices
    We apply an absolute minimum level of vol (absmin);
    and a volfloor based on lowest vol over recent history

    :param x: data
    :type x: Tx1 pd.Series

    :param days: Number of days in lookback (*default* 35)
    :type days: int

    :param min_periods: The minimum number of observations (*default* 10)
    :type min_periods: int

    :param vol_abs_min: The size of absolute minimum (*default* =0.0000000001)
      0.0= not used
    :type absmin: float or None

    :param vol_floor Apply a floor to volatility (*default* True)
    :type vol_floor: bool

    :param floor_min_quant: The quantile to use for volatility floor (eg 0.05
      means we use 5% vol) (*default 0.05)
    :type floor_min_quant: float

    :param floor_days: The lookback for calculating volatility floor, in days
      (*default* 500)
    :type floor_days: int

    :param floor_min_periods: Minimum observations for floor - until reached
      floor is zero (*default* 100)
    :type floor_min_periods: int

    :returns: pd.DataFrame -- volatility measure
    """

    # Standard deviation will be nan for first 10 non nan values
    vol = simple_ewvol_calc(daily_returns, days=days, min_periods=min_periods)
    vol = apply_min_vol(vol, vol_abs_min=vol_abs_min)

    if vol_floor:
        vol = apply_vol_floor(
            vol,
            floor_min_quant=floor_min_quant,
            floor_min_periods=floor_min_periods,
            floor_days=floor_days,
        )

    if backfill:
        # use the first vol in the past, sort of cheating
        vol = backfill_vol(vol)

    return vol


def apply_min_vol(vol: pd.Series, vol_abs_min: float = 0.0000000001) -> pd.Series:
    vol[vol < vol_abs_min] = vol_abs_min

    return vol


def apply_vol_floor(
    vol: pd.Series,
    floor_min_quant: float = 0.05,
    floor_min_periods: int = 100,
    floor_days: int = 500,
) -> pd.Series:
    # Find the rolling 5% quantile point to set as a minimum
    vol_min = vol.rolling(min_periods=floor_min_periods, window=floor_days).quantile(
        q=floor_min_quant
    )

    # set this to zero for the first value then propagate forward, ensures
    # we always have a value
    vol_min.iloc[0] = 0.0
    vol_min.ffill(inplace=True)

    # apply the vol floor
    vol_floored = np.maximum(vol, vol_min)

    return vol_floored


def backfill_vol(vol: pd.Series) -> pd.Series:
    # have to fill forwards first, as it's only the start we want to
    # backfill, eg before any value available
    vol_forward_fill = vol.ffill()
    vol_backfilled = vol_forward_fill.bfill()

    return vol_backfilled


def mixed_vol_calc(
    daily_returns: pd.Series,
    days: int = 35,
    min_periods: int = 10,
    slow_vol_years: int = 20,
    proportion_of_slow_vol: float = 0.3,
    vol_abs_min: float = 0.0000000001,
    backfill: bool = False,
    **ignored_kwargs,
) -> pd.Series:
    """
    Robust exponential volatility calculation, assuming daily series of prices
    We apply an absolute minimum level of vol (absmin);
    and a volfloor based on lowest vol over recent history

    :param x: data
    :type x: Tx1 pd.Series

    :param days: Number of days in lookback (*default* 35)
    :type days: int

    :param min_periods: The minimum number of observations (*default* 10)
    :type min_periods: int

    :param vol_abs_min: The size of absolute minimum (*default* =0.0000000001)
      0.0= not used
    :type absmin: float or None

    :param vol_floor Apply a floor to volatility (*default* True)
    :type vol_floor: bool

    :param floor_min_quant: The quantile to use for volatility floor (eg 0.05
      means we use 5% vol) (*default 0.05)
    :type floor_min_quant: float

    :param floor_days: The lookback for calculating volatility floor, in days
      (*default* 500)
    :type floor_days: int

    :param floor_min_periods: Minimum observations for floor - until reached
      floor is zero (*default* 100)
    :type floor_min_periods: int

    :returns: pd.DataFrame -- volatility measure
    """

    # Standard deviation will be nan for first 10 non nan values
    vol = simple_ewvol_calc(daily_returns, days=days, min_periods=min_periods)

    slow_vol_days = slow_vol_years * BUSINESS_DAYS_IN_YEAR
    long_vol = vol.ewm(span=slow_vol_days).mean()

    vol = long_vol * proportion_of_slow_vol + vol * (1 - proportion_of_slow_vol)

    vol = apply_min_vol(vol, vol_abs_min=vol_abs_min)

    if backfill:
        # use the first vol in the past, sort of cheating
        vol = backfill_vol(vol)

    return vol


def simple_ewvol_calc(
    daily_returns: pd.Series, days: int = 35, min_periods: int = 10, **ignored_kwargs
) -> pd.Series:
    # Standard deviation will be nan for first 10 non nan values
    vol = daily_returns.ewm(adjust=True, span=days, min_periods=min_periods).std()

    return vol


def simple_vol_calc(
    daily_returns: pd.Series, days: int = 25, min_periods: int = 10, **ignored_kwargs
) -> pd.Series:
    # Standard deviation will be nan for first 10 non nan values
    vol = daily_returns.rolling(days, min_periods=min_periods).std()

    return vol


def har_vol_calc(
    daily_returns: pd.Series,
    vol_days_short: int = 5,
    vol_days_medium: int = 22,
    vol_days_long: int = 66,
    har_weights: tuple = (0.4, 0.3, 0.3),
    min_periods: int = 10,
    vol_abs_min: float = 0.0000000001,
    backfill: bool = False,
    **ignored_kwargs,
) -> pd.Series:
    """
    HAR-style (Corsi 2009) daily volatility, assuming a daily series of returns.

    The Heterogeneous AutoRegressive model blends volatility measured over
    short/medium/long horizons, reflecting traders acting on daily, weekly and
    monthly views. Corsi builds it on intraday realized volatility with a fitted
    regression. We have only daily returns and want a parameter-light estimator,
    so we make two documented adaptations:

    1. Each horizon component is an EWM standard deviation of daily returns (the
       same construction as ``simple_ewvol_calc``) rather than an aggregate of
       intraday realized variance. A single daily return is too noisy to serve
       as a true 1-day realized-vol component, so the shortest horizon uses a
       ~1-week EWM (``vol_days_short=5``) as the daily-vol proxy; the medium and
       long horizons (~1 month / ~1 quarter, 22 / 66 business days) approximate
       the weekly- and monthly-aggregated realized-vol horizons of the original.
    2. No regression is fitted. Components are combined with fixed weights
       (``har_weights``, default ``0.4 / 0.3 / 0.3`` in the spirit of typical
       HAR-RV coefficient ratios). The weights are normalised to sum to one so
       the output stays at the daily-vol level of its components: it is a
       weighted average of estimates of the same quantity, not a sum of
       variances, so it is directly commensurate with ``simple_ewvol_calc`` and
       can be dropped in for position sizing without a level bias.

    Strictly causal: pandas ``ewm(...).std()`` at time t uses only observations
    up to and including t, so each component - and therefore the blend - depends
    only on data at or before the estimation point. Future returns never affect
    a past estimate.

    ``days`` from the standard volatility config is intentionally not used (HAR
    is inherently multi-horizon); it is absorbed by ``ignored_kwargs``.

    Unlike ``robust_vol_calc`` this applies only the absolute minimum vol, NOT
    the rolling quantile vol floor - so in ultra-low-vol regimes it can size
    positions larger than the floored estimators would. Intentional (parameter-
    light), but not position-sizing-identical to the floored siblings there.

    :param daily_returns: Tx1 series of daily returns (not % returns)
    :param vol_days_short: EWM span for the short (daily-proxy) horizon
      (*default* 5)
    :param vol_days_medium: EWM span for the medium (weekly-proxy) horizon
      (*default* 22)
    :param vol_days_long: EWM span for the long (monthly-proxy) horizon
      (*default* 66)
    :param har_weights: Weights for (short, medium, long); normalised to sum to
      one (*default* (0.4, 0.3, 0.3))
    :param min_periods: The minimum number of observations (*default* 10)
    :param vol_abs_min: The size of absolute minimum (*default* 1e-10)
    :param backfill: Backfill the leading NaN estimates (*default* False)
    :returns: Tx1 pd.Series -- daily volatility measure aligned to the input
    """

    # Each component is standard deviation, nan for the first min_periods
    # values; all three share min_periods so they turn non-nan on the same date
    vol_short = simple_ewvol_calc(
        daily_returns, days=vol_days_short, min_periods=min_periods
    )
    vol_medium = simple_ewvol_calc(
        daily_returns, days=vol_days_medium, min_periods=min_periods
    )
    vol_long = simple_ewvol_calc(
        daily_returns, days=vol_days_long, min_periods=min_periods
    )

    weights = np.array(har_weights, dtype=float)
    weights = weights / weights.sum()

    vol = weights[0] * vol_short + weights[1] * vol_medium + weights[2] * vol_long

    vol = apply_min_vol(vol, vol_abs_min=vol_abs_min)

    if backfill:
        # use the first vol in the past, sort of cheating
        vol = backfill_vol(vol)

    return vol
