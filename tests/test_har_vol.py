import numpy as np
import pandas as pd

from sysquant.estimators.vol import har_vol_calc, simple_ewvol_calc


def _returns_series(values):
    index = pd.bdate_range(start="2000-01-01", periods=len(values))
    return pd.Series(values, index=index)


def _random_returns(n, sigma, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, sigma, size=n)


def test_har_vol_is_strictly_causal():
    values = _random_returns(300, sigma=1.0, seed=1)
    baseline = har_vol_calc(_returns_series(values))

    cut = 200
    modified_values = values.copy()
    # perturb only the future - strictly after the cut point
    modified_values[cut:] = modified_values[cut:] + 50.0
    modified = har_vol_calc(_returns_series(modified_values))

    # estimates before the cut use only data < cut, so must be bitwise identical
    # (Series.equals treats NaNs in the same location as equal)
    assert baseline.iloc[:cut].equals(modified.iloc[:cut])
    # sanity: the future perturbation actually did change later estimates
    assert not baseline.iloc[cut:].equals(modified.iloc[cut:])


def test_har_vol_level_commensurate_with_simple_ewvol():
    low = _random_returns(1000, sigma=0.5, seed=2)
    high = _random_returns(1000, sigma=2.0, seed=3)
    returns = _returns_series(np.concatenate([low, high]))

    har = har_vol_calc(returns)
    simple = simple_ewvol_calc(returns, days=35, min_periods=10)

    # compare long-run means over the warmed-up region
    ratio = har.iloc[100:].mean() / simple.iloc[100:].mean()
    assert 0.75 < ratio < 1.25


def test_har_vol_responds_to_regime_jump_and_is_smoother_than_5d():
    low = _random_returns(500, sigma=0.5, seed=4)
    high = _random_returns(500, sigma=2.5, seed=5)
    returns = _returns_series(np.concatenate([low, high]))

    har = har_vol_calc(returns)
    vol5 = simple_ewvol_calc(returns, days=5, min_periods=10)

    low_regime = har.iloc[100:500].mean()
    high_regime = har.iloc[800:].mean()  # fully settled portion of high regime
    # directionally moves toward the new, higher level
    assert high_regime > low_regime * 1.5

    # within the settled high-vol regime the blend is smoother than pure 5d vol
    assert har.iloc[700:].std() < vol5.iloc[700:].std()


def test_har_vol_plumbing_nans_min_periods_and_floor():
    values = _random_returns(200, sigma=1.0, seed=6)
    values[0] = np.nan  # returns from price.diff() start with a NaN
    returns = _returns_series(values)

    min_periods = 10
    vol = har_vol_calc(returns, min_periods=min_periods)

    # leading estimates are NaN until min_periods observations are seen
    assert vol.iloc[:min_periods].isna().all()
    # no NaNs remain after the warmup
    assert vol.iloc[min_periods + 1 :].notna().all()

    # a larger min_periods pushes the first valid estimate further out
    strict = har_vol_calc(returns, min_periods=25)
    assert strict.iloc[:25].isna().all()
    assert strict.iloc[26:].notna().all()

    # the absolute floor is applied to every estimate
    floored = har_vol_calc(returns, vol_abs_min=5.0)
    assert (floored.dropna() == 5.0).all()
