"""Congress signal: follow disclosed buys, only after they are public.

Honest timing (the part his first video got wrong):
  * A trade is unknowable until its filing is posted -> `filing_date` is when we learn it.
  * We then buy at the CLOSE of the next trading day (one day of lag, no same-day fills).
  * We sell the same way, after the SAME member discloses selling that ticker,
    or after `max_hold_days`, whichever comes first.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

COST_PER_SIDE = 0.0005  # 5 bps each way; conservative for a retail account


@dataclass(frozen=True)
class Position:
    ticker: str
    member: str
    entry: pd.Timestamp
    exit: pd.Timestamp


def _next_day(days: pd.DatetimeIndex, t: pd.Timestamp) -> pd.Timestamp | None:
    """First trading day strictly after t."""
    i = days.searchsorted(t, side="right")
    return days[i] if i < len(days) else None


def build_positions(trades: pd.DataFrame, days: pd.DatetimeIndex, max_hold_days: int = 365) -> list[Position]:
    t = trades[(trades.asset_type == "ST") & trades.side.isin(["buy", "sell"])].dropna(
        subset=["filing_date", "ticker"])
    sells = t[t.side == "sell"].groupby(["member", "ticker"])["filing_date"].apply(sorted).to_dict()
    out: list[Position] = []
    # One position per (member, ticker, filing): ignore repeat buys while already held.
    for (member, ticker), g in t[t.side == "buy"].groupby(["member", "ticker"]):
        held_until: pd.Timestamp | None = None
        for filed in sorted(g.filing_date.unique()):
            filed = pd.Timestamp(filed)
            entry = _next_day(days, filed)
            if entry is None or (held_until is not None and entry <= held_until):
                continue
            later_sells = [s for s in sells.get((member, ticker), []) if s > filed]
            exit_signal = _next_day(days, later_sells[0]) if later_sells else None
            cap = _next_day(days, entry + pd.Timedelta(days=max_hold_days))
            exit_ = min([d for d in (exit_signal, cap) if d is not None], default=days[-1])
            out.append(Position(ticker, member, entry, exit_))
            held_until = exit_
    return out


def equal_weight_returns(positions: list[Position], prices: pd.DataFrame, cost: float = COST_PER_SIDE) -> pd.Series:
    """Daily returns of an equal-weight book over the unique tickers held that day.

    Return on day d is earned only by positions entered BEFORE d (entry day itself earns 0,
    because we buy at that day's close). Idle days are cash (0%).
    """
    rets = prices.pct_change()
    days = prices.index
    held = pd.DataFrame(False, index=days, columns=prices.columns)
    fee = pd.Series(0.0, index=days)
    for p in positions:
        if p.ticker not in prices.columns:
            continue
        mask = (days > p.entry) & (days <= p.exit)
        held.loc[mask, p.ticker] = True
        fee.loc[p.entry] += cost
        fee.loc[p.exit] += cost
    held &= rets.notna()  # no price that day (delisted / gap) -> not counted as held
    n = held.sum(axis=1)
    book = (rets.where(held).sum(axis=1) / n.replace(0, np.nan)).fillna(0.0)
    # Fees are spread over the book size so they cost the portfolio what they would in $.
    turnover_cost = (fee / n.clip(lower=1)).where(n > 0, 0.0)
    return book - turnover_cost


def trade_returns(positions: list[Position], prices: pd.DataFrame, bench: pd.Series) -> pd.DataFrame:
    """Per-trade return vs buying SPY over the same dates (net of round-trip costs)."""
    rows = []
    for p in positions:
        if p.ticker not in prices.columns:
            continue
        s = prices[p.ticker]
        a, b = s.get(p.entry), s.get(p.exit)
        ba, bb = bench.get(p.entry), bench.get(p.exit)
        if any(pd.isna(x) for x in (a, b, ba, bb)) or a <= 0:
            continue
        rows.append({"ticker": p.ticker, "member": p.member, "entry": p.entry, "exit": p.exit,
                     "ret": b / a - 1 - 2 * COST_PER_SIDE, "bench": bb / ba - 1})
    return pd.DataFrame(rows)
