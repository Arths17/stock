# stock

A research-first trading bot. Most retail trading signals fail honest tests, so nothing
trades live until it beats the S&P 500 (SPY) **and** hundreds of random portfolios on a
sealed holdout that is used once.

## Design

- **Bot decides, Claude executes.** Python code computes signals and writes order
  *intents* (`src/stockbot/orders.py`). A scheduled Claude task reads them, re-checks
  `guardrails.check_order`, and places orders through the Robinhood MCP.
- **One account only.** `config.ALLOWED_ACCOUNT` (Robinhood "MCP", `635722408`). Any other
  account is rejected. No shorts, options, or margin.
- **Hard limits** (`config.py`): $25 per order, $50 per day, 15% drawdown kill switch,
  `live_enabled=False` until a signal passes the holdout.
- **Cadence.** Hourly risk checks in market hours, daily signal runs, quarterly rebalances.

## Honest-testing rules (from the LosingLoonies videos)

1. No look-ahead: features must be available strictly before the decision (`backtest/lookahead.py`).
2. Survivorship-free universe, including delisted names.
3. Sealed holdout, run once; stricter bar for each variation tried.
4. Compare to SPY, and to random portfolios (`backtest/metrics.py`).
5. Judge by Sharpe, not just return.

## Signals planned

Congress trades (enter after filing), Graham value, Reddit (DD-only / niche clusters),
Fear & Greed / VIX as risk filters, LSTM/XGBoost, Truth Social (backtest only: needs
sub-minute reaction), satellite (research only).

## Dev

```bash
pip install -e '.[dev]' && pytest
```

Not financial advice. Expect most signals to fail; the harness exists to find that out cheaply.
