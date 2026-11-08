"""Graham value backtest on the point-in-time S&P 500 universe.

Usage: python scripts/run_graham_backtest.py 2018-01-01 2023-12-31
Pre-registered: dev 2018-2023; sealed holdout 2024-01-01+ is run ONCE, only if dev beats SPY and
the all-eligible control and random picks.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from stockbot.backtest.metrics import cagr, sharpe  # noqa: E402
from stockbot.data.sec_eps import load_eps  # noqa: E402
from stockbot.data.sp500 import load_intervals, members_on  # noqa: E402
from stockbot.signals.graham import eps_history_asof, intrinsic_value, select  # noqa: E402
from stockbot.signals.congress import COST_PER_SIDE  # noqa: E402


def load_all():
    iv = load_intervals(ROOT / "data/sp500/ticker_start_end.csv")
    mk = {}
    for f in (ROOT / "data/market").glob("*.csv"):
        if f.stat().st_size > 5:
            mk[f.stem] = pd.read_csv(f, index_col=0, parse_dates=True)
    eps, _ = load_eps(sorted(mk), cache=ROOT / "data/sec")
    return iv, mk, eps


def stats(name, r):
    e = (1 + r).cumprod()
    print(f"{name:26s} total {e.iloc[-1]-1:+8.1%}  CAGR {cagr(e):+6.1%}  Sharpe {sharpe(r):5.2f}  "
          f"maxDD {(e/e.cummax()-1).min():6.1%}")


def main(start: str, end: str, sims: int = 300) -> None:
    iv, mk, eps = load_all()
    adj = pd.DataFrame({t: d["adjclose"] for t, d in mk.items()}).sort_index()
    rets = adj.pct_change(fill_method=None)
    days = adj.index[adj["SPY"].notna()]
    win = days[(days >= start) & (days <= end)]
    # first trading day of each calendar quarter inside the window
    rebal = [g.iloc[0] for _, g in pd.Series(win, index=win).groupby([win.year, win.quarter])]
    rng = np.random.default_rng(0)

    book = {"strategy": pd.Series(0.0, index=win), "all_eligible": pd.Series(0.0, index=win)}
    rand_books = [pd.Series(0.0, index=win) for _ in range(sims)]
    prev = {"strategy": set(), "all_eligible": set()}
    n_elig, n_sel, member_cov = [], [], []

    for k, r0 in enumerate(rebal):
        r1 = rebal[k + 1] if k + 1 < len(rebal) else win[-1]
        sig = days[days.get_loc(r0) - 1]                       # signal uses the PRIOR close
        members = members_on(iv, sig)
        rows = {}
        for t in members & set(mk) & set(eps):
            m = mk[t]
            i = m.index.searchsorted(sig, side="right") - 1
            if i < 0 or (sig - m.index[i]).days > 5:
                continue
            price = m["close"].iloc[i] * m["split_after"].iloc[i]    # price as quoted that day
            ivv = intrinsic_value(eps_history_asof(eps[t], sig, m["split_after"]))
            rows[t] = (price, ivv)
        vals = pd.DataFrame(rows, index=["price", "iv"]).T if rows else pd.DataFrame(columns=["price", "iv"])
        member_cov.append(len(rows) / max(len(members), 1))
        eligible = list(vals.dropna().query("iv > 0").index)
        chosen = select(vals) if len(vals) else []
        n_elig.append(len(eligible)); n_sel.append(len(chosen))
        period = win[(win > r0) & (win <= r1)]

        def run(name, names, store):
            names = [n for n in names if n in rets.columns]
            if not names:
                prev[name] = set() if name in prev else None
                return
            ew = rets.loc[period, names].mean(axis=1).fillna(0.0)
            old = prev.get(name, set()) if name in prev else set()
            turn = len(set(names) ^ old) / max(len(names), 1)
            ew.iloc[0] -= COST_PER_SIDE * turn
            store.loc[period] = ew.values
            if name in prev:
                prev[name] = set(names)

        run("strategy", chosen, book["strategy"])
        run("all_eligible", eligible, book["all_eligible"])
        if chosen:
            for s in range(sims):
                pick = list(rng.choice(eligible, size=min(len(chosen), len(eligible)), replace=False))
                rb = rand_books[s]
                rb.loc[period] = rets.loc[period, [p for p in pick if p in rets.columns]].mean(axis=1).fillna(0.0).values

    print(f"window {start}..{end}; {len(rebal)} quarterly rebalances")
    print(f"S&P members with price+EPS data (avg): {np.mean(member_cov):.0%}  "
          f"(rest are delisted/renamed or lack XBRL EPS: survivorship bias)")
    print(f"eligible names/qtr (EPS>0): avg {np.mean(n_elig):.0f};  selected (price<50% of value): avg {np.mean(n_sel):.1f}, "
          f"quarters with none: {sum(1 for n in n_sel if n == 0)}/{len(n_sel)}")
    stats("Graham value (<50% IV)", book["strategy"])
    stats("All eligible, equal wt", book["all_eligible"])
    spy = rets.loc[win, "SPY"].fillna(0); rsp = rets.loc[win, "RSP"].fillna(0)
    stats("SPY", spy); stats("RSP", rsp)
    tot = (1 + book["strategy"]).prod() - 1
    rtot = np.array([(1 + b).prod() - 1 for b in rand_books])
    print(f"random picks, same count, same dates ({sims} sims): median {np.median(rtot):+.1%} "
          f"[5-95%: {np.percentile(rtot,5):+.1%}..{np.percentile(rtot,95):+.1%}]; strategy beats {(tot > rtot).mean():.0%}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
