# Graham value signal: development-window results (2018-2023)

Pre-registered rules (set before looking at any result): V = EPS x (8.5 + 2g), g = 5-yr EPS CAGR
clipped to [0, 10]%, annual diluted EPS as first filed (SEC companyfacts, real filing dates), put on
the signal date's share basis (split-adjusted). Buy when price < 50% of V, EPS > 0, cheapest 25 by
price/V, S&P 500 members as of the signal date, quarterly rebalance, signal on the prior close,
5 bps per side. Sealed holdout 2024-01-01+: NOT run (dev did not pass).

| | Total | CAGR | Sharpe | Max DD |
|---|---|---|---|---|
| Graham value (<50% of V) | +98.7% | +12.1% | 0.53 | -49.6% |
| All eligible, equal weight (control) | +87.1% | +11.0% | 0.59 | -39.4% |
| SPY | +96.9% | +11.9% | 0.66 | -33.7% |
| RSP | +74.0% | +9.6% | 0.54 | -39.0% |

Random picks (same count, same dates, 300 sims): median +85.3%; strategy beat 74% (bar: 95%).
Selected names averaged 24.8 per quarter; no quarter was empty.

Verdict: same return as SPY with a worse Sharpe and a much deeper drawdown; not better than random at
the pre-set bar. Not eligible for live trading.

Why (observed, not tuned): trailing annual EPS is a poor value input. March 2020 picks were airlines
and cruise lines on pre-COVID earnings; 2022 picks included names whose EPS was inflated by one-off
gains (EBAY, BIO, NRG). Cheap-on-stale-earnings is a value trap, which a Graham screen cannot tell apart.

Caveats: only 86% of S&P members per date had price + EPS data; delisted/renamed names are missing
(108 of 709 had no Yahoo history), so results are biased upward. Annual (not TTM) EPS; GAAP, unadjusted.
