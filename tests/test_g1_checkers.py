"""Tests for the pure G1b continuity/freshness assertions (no DB, no IB)."""
import pandas as pd

from analysis.research_harness.g1b_stitch_check import (
    SEED_END,
    continuity_failures,
    freshness_failures,
)

HEALTHY_START = "2024-01-01"
HEALTHY_END = "2026-07-10"


def _healthy_index() -> pd.DatetimeIndex:
    return pd.bdate_range(HEALTHY_START, HEALTHY_END)


def _index_with_hole(hole_bdays: int) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    """Healthy index with `hole_bdays` consecutive post-boundary business days
    removed; returns (index-with-hole, the removed dates)."""
    index = _healthy_index()
    post = index[index > SEED_END]
    hole = post[20 : 20 + hole_bdays]
    return index.drop(hole), hole


def test_empty_index_fails_as_no_stitched_data():
    failures = continuity_failures(pd.DatetimeIndex([]), [])
    assert len(failures) == 1
    assert "no stitched data" in failures[0]


def test_single_point_before_boundary_only_fails():
    dates = pd.DatetimeIndex([pd.Timestamp("2024-01-05")])
    failures = continuity_failures(dates, [])
    assert len(failures) == 1
    assert "no stitched data" in failures[0]


def test_post_boundary_only_series_fails_boundary_anchor():
    dates = pd.bdate_range("2024-06-03", HEALTHY_END)
    failures = continuity_failures(dates, [])
    assert len(failures) == 1
    assert "no stitched data" in failures[0]


def test_healthy_business_day_series_passes():
    assert continuity_failures(_healthy_index(), []) == []


def test_unexempted_ten_business_day_hole_reports_the_gap():
    dates, _hole = _index_with_hole(10)
    failures = continuity_failures(dates, [])
    assert len(failures) == 1
    assert "10 business days missing" in failures[0]


def test_exempted_hole_passes_gap_and_coverage():
    index = _healthy_index()
    post = index[index > SEED_END]
    dates, hole = _index_with_hole(10)
    # window starts at the last observation before the hole (existing
    # semantics: exempt iff previous >= start and current <= end + 4 days);
    # coverage must still pass because exempt business days are excluded
    exemptions = [(post[19], hole[-1])]
    assert continuity_failures(dates, exemptions) == []


def test_sparse_weekly_series_fails_coverage_only():
    pre = pd.bdate_range(HEALTHY_START, SEED_END)
    # weekly Wednesdays: 4-business-day gaps never trip MAX_GAP_BDAYS,
    # but only ~20% of post-boundary business days are covered
    post_weekly = pd.date_range(
        SEED_END + pd.Timedelta(days=1), HEALTHY_END, freq="W-WED"
    )
    failures = continuity_failures(pre.append(post_weekly), [])
    assert len(failures) == 1
    assert "coverage" in failures[0]


def test_freshness_flags_instrument_ending_long_before_another():
    last_dates = {
        "CORN": pd.Timestamp("2026-07-10"),
        "V2X": pd.Timestamp("2026-06-01"),
    }
    failures = freshness_failures(last_dates)
    assert len(failures) == 1
    assert "V2X" in failures[0]
    assert "stale" in failures[0]


def test_freshness_passes_when_all_within_window():
    last_dates = {
        "CORN": pd.Timestamp("2026-07-10"),
        "V2X": pd.Timestamp("2026-07-07"),
    }
    assert freshness_failures(last_dates) == []
