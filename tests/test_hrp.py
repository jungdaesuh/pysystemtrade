import numpy as np
import pandas as pd
import pytest

from sysquant.estimators.estimates import Estimates
from sysquant.estimators.correlations import correlationEstimate
from sysquant.estimators.mean_estimator import meanEstimates
from sysquant.estimators.stdev_estimator import stdevEstimates
from sysquant.optimisation.optimisers.hrp import hrp_optimisation


def _build_estimates(corr_values, stdev_values, mean_values):
    assets = [f"A{i}" for i in range(len(stdev_values))]
    corr_df = pd.DataFrame(corr_values, index=assets, columns=assets)
    corr = correlationEstimate.from_pd(corr_df)
    stdev = stdevEstimates(list(zip(assets, stdev_values)))
    mean = meanEstimates(list(zip(assets, mean_values)))
    return Estimates(
        correlation=corr,
        mean=mean,
        stdev=stdev,
        data_length=252,
        frequency="B",
    )


def test_hrp_weights_sum_to_one_and_positive():
    corr = np.array(
        [[1.0, 0.3, 0.1], [0.3, 1.0, 0.2], [0.1, 0.2, 1.0]],
        dtype=float,
    )
    stdev = np.array([0.2, 0.15, 0.25], dtype=float)
    mean = np.array([0.05, 0.04, 0.06], dtype=float)
    estimates = _build_estimates(corr, stdev, mean)

    result = hrp_optimisation(estimates)
    weights = result.weights
    total = sum(weights.values())

    assert pytest.approx(total, rel=1e-6) == 1.0
    assert all(weight >= 0 for weight in weights.values())


def test_hrp_falls_back_to_equal_weights_on_invalid_covariance():
    corr = np.array([[1.0, np.nan], [np.nan, 1.0]])
    stdev = np.array([0.2, 0.3])
    mean = np.array([0.05, 0.06])
    estimates = _build_estimates(corr, stdev, mean)

    result = hrp_optimisation(estimates)
    weights = list(result.weights.values())
    assert pytest.approx(weights[0], rel=1e-6) == 0.5
    assert pytest.approx(weights[1], rel=1e-6) == 0.5


def test_hrp_single_asset_returns_full_weight():
    corr = np.array([[1.0]])
    stdev = np.array([0.2])
    mean = np.array([0.05])
    estimates = _build_estimates(corr, stdev, mean)

    result = hrp_optimisation(estimates)
    weights = list(result.weights.values())
    assert weights == [1.0]
