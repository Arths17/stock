# Congress signal: development-window results (2018-2023)

Data: official House Clerk PTR filings (5,433 filings, 21,718 clean stock trades, 212 members),
Yahoo adjusted closes. Senate is not included yet. Pre-registered: dev window 2018-01..2023-12,
sealed holdout 2024-01..now (NOT run: the signal failed dev).

Timing: learn of a trade on its `filing_date`, buy the close of the next trading day, sell the
close of the day after the same member discloses selling that ticker (cap 365d). 5 bps per side.

| | Total | CAGR | Sharpe | Max DD |
|---|---|---|---|---|
| Congress (until-sell) | +84.4% | +10.8% | 0.57 | -38.3% |
| Congress (60-day hold, context) | +99.7% | +12.2% | 0.63 | -37.9% |
| SPY | +95.5% | +11.9% | 0.65 | -33.7% |
| RSP (equal-weight S&P) | +72.8% | +9.6% | 0.54 | -39.0% |

Per trade (until-sell): mean +8.56% vs SPY +8.93%, median excess -2.22%, beat SPY 43%.
Random tickers on the same dates averaged +12.7%; the strategy beat 0% of 500 random draws
(60-day variant: 4%).

Caveats: 11% of buy positions were unpriced (delisted/acquired) and dropped, so everything here
carries survivorship bias; the random pool shares it. Equal-weight, amounts ignored, House only.

Verdict: no edge on honest timing, consistent with the source video. Not eligible for live trading.
