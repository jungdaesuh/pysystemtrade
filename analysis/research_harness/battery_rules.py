"""Candidate trading rules under battery evaluation (lit review 2026-07-18).

Rules live here until a pre-registered battery verdict adopts them; only
adopted rules graduate to systems/provided/rules/.
"""


def seasonal_carry(raw_carry, span_days=256):
    """Annualised carry with the seasonal cycle removed: simple rolling
    12-month mean of raw carry (AFTS seasonally-adjusted carry treatment —
    a plain mean over one full cycle cancels an annual seasonal component,
    which an EWMA cannot).

    :param raw_carry: annualised SR of rolldown from rawdata.raw_carry
    :return: unscaled forecast
    """
    return raw_carry.rolling(span_days, min_periods=span_days // 2).mean()
