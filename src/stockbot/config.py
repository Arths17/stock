"""Hard limits. Change these here, in code review, never at runtime."""
from dataclasses import dataclass

# The ONLY account this project may ever place orders on (Robinhood nickname "MCP").
ALLOWED_ACCOUNT = "635722408"


@dataclass(frozen=True)
class Limits:
    max_order_usd: float = 25.0       # per single order
    max_daily_usd: float = 50.0       # total new buys per day
    kill_drawdown: float = 0.15       # halt if equity falls this far below its peak
    allow_shorts: bool = False        # no shorting, no options, no margin
    live_enabled: bool = False        # live orders stay OFF until a signal passes the holdout


LIMITS = Limits()
