"""Backtest the Congress signal over [start, end] and compare to SPY, RSP and random picks.

Usage: python scripts/run_congress_backtest.py 2018-01-01 2023-12-31 [max_hold_days]
Pre-registered: dev window 2018-2023; sealed holdout 2024-01-01 onward, run ONCE.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stockbot.backtest.metrics import cagr, sharpe  # noqa: E402
from stockbot.signals.congress import COST_PER_SIDE, build_positions, equal_weight_returns, trade_returns  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main(start: str, end: str, max_hold: int, sims: int = 500) -> None:
    trades = pd.read_csv(ROOT / "data/congress/house_trades_clean.csv",
                         parse_dates=["transaction_date", "notification_date", "filing_date"])
    px = pd.read_csv(ROOT / "data/prices_all.csv", index_col=0, parse_dates=True)
    px = px.loc[start:end]
    bench, rsp = px["SPY"], px["RSP"]
    days = px.index[px["SPY"].notna()]
    trades = trades[(trades.filing_date >= start) & (trades.filing_date <= end)]

    pos_all = build_positions(trades, days, max_hold)
    priced = [p for p in pos_all if p.ticker in px.columns]
    print(f"window {start}..{end}  max_hold={max_hold}d")
    print(f"buy positions: {len(pos_all)}  priced: {len(priced)} ({len(priced)/max(len(pos_all),1):.0%})  "
          f"unpriced (delisted/missing, dropped): {len(pos_all)-len(priced)}")

    r = equal_weight_returns(priced, px)
    eq = (1 + r).cumprod()
    live = r != 0
    print(f"days invested: {live.mean():.0%} of window (idle days = cash)")
    for name, ser in [("Congress", r), ("SPY", bench.pct_change().fillna(0)), ("RSP", rsp.pct_change().fillna(0))]:
        e = (1 + ser).cumprod()
        print(f"{name:9s} total {e.iloc[-1]-1:+7.1%}  CAGR {cagr(e):+6.1%}  Sharpe {sharpe(ser):5.2f}  "
              f"maxDD {(e/e.cummax()-1).min():6.1%}")

    tr = trade_returns(priced, px, bench)
    ex = tr.ret - tr.bench
    print(f"trades {len(tr)}  mean {tr.ret.mean():+.2%} vs SPY {tr.bench.mean():+.2%}  "
          f"mean excess {ex.mean():+.2%}  median excess {ex.median():+.2%}  beat SPY {(ex>0).mean():.0%}")

    # Random baseline: same dates, random priced tickers instead of the congressional pick.
    rng = np.random.default_rng(0)
    cols = [c for c in px.columns if c not in ("SPY", "RSP")]
    sample = tr.sample(min(len(tr), 3000), random_state=0)
    ent = px.loc[sample.entry, cols].to_numpy()
    ext = px.loc[sample.exit, cols].to_numpy()
    ok = np.isfinite(ent) & np.isfinite(ext) & (ent > 0)
    rand_mean = np.empty(sims)
    for k in range(sims):
        picks = [rng.choice(np.flatnonzero(ok[i])) for i in range(len(sample))]
        a = ent[np.arange(len(sample)), picks]; b = ext[np.arange(len(sample)), picks]
        rand_mean[k] = (b / a - 1 - 2 * COST_PER_SIDE).mean()
    strat = sample.ret.mean()
    print(f"random-ticker baseline (same dates, {sims} sims): mean {rand_mean.mean():+.2%} "
          f"[5%..95% {np.percentile(rand_mean,5):+.2%}..{np.percentile(rand_mean,95):+.2%}]; "
          f"strategy beats {(strat > rand_mean).mean():.0%} of them")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 365)
