import math

import pandas as pd
import pytest

from stockbot.signals.graham import eps_history_asof, intrinsic_value, select


def test_zero_growth_formula():
    assert intrinsic_value([2.0] * 6) == pytest.approx(2.0 * 8.5)


def test_growth_is_capped_at_ten_percent():
    # EPS doubles every year: raw g = 100%, must cap at 10 -> 8.5 + 20 = 28.5
    assert intrinsic_value([1, 2, 4, 8, 16, 32]) == pytest.approx(32 * 28.5)


def test_negative_or_missing_eps_gives_nan():
    assert math.isnan(intrinsic_value([1, 1, 1, 1, 1, -0.5]))
    assert math.isnan(intrinsic_value([]))


def test_shrinking_earnings_do_not_get_a_negative_growth_bonus():
    assert intrinsic_value([4, 3, 3, 2, 2, 1]) == pytest.approx(1 * 8.5)


def test_only_eps_filed_before_signal_date_is_used():
    df = pd.DataFrame({"end": pd.to_datetime(["2019-12-31", "2020-12-31"]),
                       "filed": pd.to_datetime(["2020-02-20", "2021-02-20"]), "val": [5.0, 9.0]})
    sa = pd.Series(1.0, index=pd.bdate_range("2019-01-01", "2022-01-01"))
    assert eps_history_asof(df, pd.Timestamp("2021-01-15"), sa) == [5.0]   # FY2020 not public yet
    assert eps_history_asof(df, pd.Timestamp("2021-03-01"), sa) == [5.0, 9.0]


def test_split_between_filing_and_signal_date_is_adjusted():
    # 4:1 split on 2020-09-01. EPS $12 filed Feb 2020 on the OLD share basis -> $3 after the split.
    idx = pd.bdate_range("2019-01-01", "2021-01-01")
    sa = pd.Series(1.0, index=idx)
    sa[sa.index < "2020-09-01"] = 4.0
    df = pd.DataFrame({"end": pd.to_datetime(["2019-12-31"]), "filed": pd.to_datetime(["2020-02-14"]), "val": [12.0]})
    assert eps_history_asof(df, pd.Timestamp("2020-12-01"), sa) == [pytest.approx(3.0)]


def test_select_needs_a_50_percent_margin_and_ranks_by_discount():
    v = pd.DataFrame({"price": [10, 20, 55, 30], "iv": [100, 100, 100, float("nan")]},
                     index=["CHEAP", "OK", "FAIR", "NAN"])
    assert select(v) == ["CHEAP", "OK"]
