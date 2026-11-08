import numpy as np
import pandas as pd
import pytest

from stockbot.backtest.lookahead import assert_no_lookahead, lag_one_day
from stockbot.backtest.metrics import beats_random, cagr, random_portfolio_returns, sharpe


def test_cagr_doubles_in_one_year():
    eq = pd.Series(np.linspace(100, 200, 252))
    assert cagr(eq) == pytest.approx(1.0, rel=0.02)


def test_sharpe_higher_for_smoother_returns():
    smooth = pd.Series([0.001] * 100) + pd.Series(np.random.default_rng(0).normal(0, 0.0005, 100))
    rough = pd.Series([0.001] * 100) + pd.Series(np.random.default_rng(0).normal(0, 0.02, 100))
    assert sharpe(smooth) > sharpe(rough)


def test_random_baseline_and_beats_random():
    rng = np.random.default_rng(1)
    fwd = pd.DataFrame(rng.normal(0.01, 0.05, (20, 30)))
    rand = random_portfolio_returns(fwd, n_picks=5, n_sims=200)
    assert len(rand) == 200
    assert beats_random(rand.max() + 1, rand)
    assert not beats_random(rand.min() - 1, rand)


def test_lookahead_guard_catches_same_day_data():
    t = pd.Series(pd.to_datetime(["2025-01-02"] * 2))
    ok = pd.DataFrame({"available_at": pd.to_datetime(["2025-01-01", "2025-01-01"])})
    bad = pd.DataFrame({"available_at": pd.to_datetime(["2025-01-01", "2025-01-02"])})
    assert_no_lookahead(ok, t)
    with pytest.raises(AssertionError):
        assert_no_lookahead(bad, t)


def test_lag_one_day_shifts_signal():
    s = pd.Series([1, 2, 3])
    assert lag_one_day(s).tolist()[1:] == [1, 2]
