"""Graham value signal (pre-registered parameters; do not tune on the dev window).

Intrinsic value:  V = EPS * (8.5 + 2g)   (Graham's growth formula)
  EPS = latest annual diluted EPS filed BEFORE the signal date (point-in-time)
  g   = 5-year EPS CAGR in percent, only if the oldest EPS > 0, clipped to [0, 10]; else 0
Buy rule: price < MARGIN * V, EPS > 0, ranked by price/V, at most MAX_NAMES names.
Everything is put on the share basis of the signal date, so stock splits don't fake value.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

MARGIN = 0.5      # buy below half of intrinsic value
MAX_NAMES = 25
G_CAP = 10.0      # percent per year
HISTORY = 6       # annual EPS points -> 5 growth years


def intrinsic_value(eps_oldest_to_newest: list[float]) -> float:
    eps = [float(x) for x in eps_oldest_to_newest if x is not None and not math.isnan(x)]
    if not eps or eps[-1] <= 0:
        return float("nan")
    g = 0.0
    if len(eps) >= HISTORY and eps[-HISTORY] > 0:
        g = ((eps[-1] / eps[-HISTORY]) ** (1 / (HISTORY - 1)) - 1) * 100
    g = min(max(g, 0.0), G_CAP)
    return eps[-1] * (8.5 + 2 * g)


def eps_history_asof(eps_df: pd.DataFrame, signal_date: pd.Timestamp, split_after: pd.Series) -> list[float]:
    """Last HISTORY annual EPS values filed strictly before signal_date, on signal_date's share basis."""
    known = eps_df[eps_df["filed"] < signal_date].sort_values("end").tail(HISTORY)
    if known.empty:
        return []
    sa_t = _split_after_at(split_after, signal_date)
    out = []
    for _, r in known.iterrows():
        splits_between = _split_after_at(split_after, r["filed"]) / sa_t
        out.append(r["val"] / splits_between)
    return out


def _split_after_at(split_after: pd.Series, t: pd.Timestamp) -> float:
    i = split_after.index.searchsorted(t, side="right") - 1
    return float(split_after.iloc[max(i, 0)])


def select(values: pd.DataFrame) -> list[str]:
    """values: index=ticker, columns=[price, iv]. Returns up to MAX_NAMES cheapest-vs-value tickers."""
    v = values.dropna()
    v = v[(v.iv > 0) & (v.price > 0) & (v.price < MARGIN * v.iv)]
    return list((v.price / v.iv).sort_values().head(MAX_NAMES).index)
