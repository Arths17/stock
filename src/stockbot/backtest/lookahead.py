"""Guard against look-ahead bias (the `<` vs `<=` bug that faked +51%)."""
from __future__ import annotations

import pandas as pd


def assert_no_lookahead(features: pd.DataFrame, decision_times: pd.Series) -> None:
    """Every feature row must carry an `available_at` time strictly before its decision time.

    features: needs an `available_at` column (when the data became public).
    decision_times: the time each row is used to make a decision (same index).
    """
    if "available_at" not in features.columns:
        raise ValueError("features need an `available_at` column")
    late = features["available_at"] >= decision_times.reindex(features.index)
    if late.any():
        raise AssertionError(f"{int(late.sum())} feature rows use data not yet available")


def lag_one_day(signal: pd.Series) -> pd.Series:
    """Trade tomorrow on today's signal, never the same day."""
    return signal.shift(1)
