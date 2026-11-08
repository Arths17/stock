"""Honest evaluation: Sharpe, CAGR, and a random-portfolio baseline."""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def cagr(equity: pd.Series) -> float:
    years = len(equity) / TRADING_DAYS
    if years <= 0 or equity.iloc[0] <= 0:
        return float("nan")
    return float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1)


def sharpe(daily_returns: pd.Series) -> float:
    sd = daily_returns.std()
    if not sd or np.isnan(sd):
        return float("nan")
    return float(daily_returns.mean() / sd * np.sqrt(TRADING_DAYS))


def random_portfolio_returns(
    forward_returns: pd.DataFrame, n_picks: int, n_sims: int, seed: int = 0
) -> np.ndarray:
    """Mean forward return of `n_sims` random n_picks-stock portfolios.

    forward_returns: one row per rebalance date, one column per stock (NaN = not tradable).
    Returns an array of per-simulation average returns across all dates.
    """
    rng = np.random.default_rng(seed)
    out = np.zeros(n_sims)
    for s in range(n_sims):
        per_date = []
        for _, row in forward_returns.iterrows():
            avail = row.dropna()
            if len(avail) < n_picks:
                continue
            idx = rng.choice(len(avail), size=n_picks, replace=False)
            per_date.append(avail.iloc[idx].mean())
        out[s] = np.mean(per_date) if per_date else np.nan
    return out


def beats_random(strategy_mean: float, random_means: np.ndarray, pct: float = 0.95) -> bool:
    """True only if the strategy beats `pct` of random portfolios."""
    return bool((strategy_mean > random_means).mean() >= pct)
