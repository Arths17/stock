import pandas as pd

from stockbot.signals.congress import build_positions, equal_weight_returns

DAYS = pd.bdate_range("2024-01-01", "2024-12-31")


def trades(rows):
    df = pd.DataFrame(rows, columns=["member", "ticker", "side", "filing_date"])
    df["asset_type"] = "ST"
    df["filing_date"] = pd.to_datetime(df["filing_date"])
    return df


def test_entry_is_the_day_after_filing_never_same_day():
    pos = build_positions(trades([("A", "XYZ", "buy", "2024-03-04")]), DAYS)
    assert pos[0].entry == pd.Timestamp("2024-03-05")


def test_exit_when_same_member_discloses_sale():
    t = trades([("A", "XYZ", "buy", "2024-03-04"), ("A", "XYZ", "sell", "2024-05-06"),
                ("B", "XYZ", "sell", "2024-04-01")])  # B's sale must not close A's trade
    pos = build_positions(t, DAYS)
    assert pos[0].exit == pd.Timestamp("2024-05-07")


def test_max_hold_caps_the_position():
    pos = build_positions(trades([("A", "XYZ", "buy", "2024-01-02")]), DAYS, max_hold_days=60)
    assert (pos[0].exit - pos[0].entry).days <= 63


def test_sale_filed_before_buy_is_ignored():
    t = trades([("A", "XYZ", "sell", "2024-02-01"), ("A", "XYZ", "buy", "2024-03-04")])
    assert build_positions(t, DAYS)[0].exit == DAYS[-1]


def test_entry_day_earns_nothing_and_costs_are_charged():
    prices = pd.DataFrame({"XYZ": 100.0 * (1.01 ** pd.Series(range(len(DAYS))).values)}, index=DAYS)
    pos = build_positions(trades([("A", "XYZ", "buy", "2024-03-04")]), DAYS, max_hold_days=30)
    r = equal_weight_returns(pos, prices)
    assert r.loc[pos[0].entry] <= 0          # no return on the day we buy at the close
    assert r.loc[pos[0].entry + pd.offsets.BDay(1)] > 0.009
