"""Every order intent must pass here before anything executes it."""
from __future__ import annotations

from dataclasses import dataclass

from .config import ALLOWED_ACCOUNT, LIMITS, Limits
from .orders import OrderIntent


@dataclass
class AccountState:
    equity: float
    peak_equity: float
    spent_today_usd: float = 0.0


def check_order(
    order: OrderIntent, state: AccountState, limits: Limits = LIMITS
) -> tuple[bool, str]:
    """Return (allowed, reason). Fail closed: any doubt means reject."""
    if order.account != ALLOWED_ACCOUNT:
        return False, "account is not the allowed MCP account"
    if order.side not in ("buy", "sell"):
        return False, "side must be buy or sell"
    if not (order.usd > 0):
        return False, "order size must be positive"
    if order.side == "sell" and order.usd > limits.max_order_usd * 4:
        return False, "sell size above sanity cap"
    if not order.paper and not limits.live_enabled:
        return False, "live trading is disabled"
    if state.peak_equity > 0:
        drawdown = 1 - state.equity / state.peak_equity
        if drawdown >= limits.kill_drawdown and order.side == "buy":
            return False, "kill switch: drawdown limit hit"
    if order.side == "buy":
        if order.usd > limits.max_order_usd:
            return False, "over per-order cap"
        if state.spent_today_usd + order.usd > limits.max_daily_usd:
            return False, "over daily cap"
    return True, "ok"
