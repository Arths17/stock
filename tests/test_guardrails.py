from stockbot.config import ALLOWED_ACCOUNT, Limits
from stockbot.guardrails import AccountState, check_order
from stockbot.orders import OrderIntent

STATE = AccountState(equity=500, peak_equity=500)
LIVE = Limits(live_enabled=True)


def buy(usd=10, account=ALLOWED_ACCOUNT, paper=True):
    return OrderIntent(account, "RSP", "buy", usd, "test", paper=paper)


def test_paper_buy_within_caps_ok():
    assert check_order(buy(), STATE)[0]


def test_other_account_rejected():
    ok, why = check_order(buy(account="808920755"), STATE)
    assert not ok and "account" in why


def test_live_blocked_by_default():
    assert not check_order(buy(paper=False), STATE)[0]


def test_live_allowed_when_enabled():
    assert check_order(buy(paper=False), STATE, LIVE)[0]


def test_per_order_cap():
    assert not check_order(buy(usd=26), STATE)[0]


def test_daily_cap():
    st = AccountState(equity=500, peak_equity=500, spent_today_usd=45)
    assert not check_order(buy(usd=10), st)[0]


def test_kill_switch_blocks_buys_not_sells():
    st = AccountState(equity=400, peak_equity=500)  # 20% drawdown
    assert not check_order(buy(), st)[0]
    sell = OrderIntent(ALLOWED_ACCOUNT, "RSP", "sell", 10, "test")
    assert check_order(sell, st)[0]


def test_bad_inputs_rejected():
    assert not check_order(buy(usd=0), STATE)[0]
    bad = OrderIntent(ALLOWED_ACCOUNT, "RSP", "short", 10, "test")
    assert not check_order(bad, STATE)[0]
