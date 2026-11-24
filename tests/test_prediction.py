from datetime import date

import pytest

import main
from tests.conftest import price_frame


def test_straight_line_is_extended_exactly():
    closes = [10.0 + i for i in range(30)]
    result = main.predict_future_prices(closes, days=5)
    assert result["predictions"] == [40.0, 41.0, 42.0, 43.0, 44.0]
    assert result["slope_per_day"] == pytest.approx(1.0)
    assert result["r_squared"] == pytest.approx(1.0)
    assert result["points"] == 30
    assert len(result["trend"]) == 30
    assert result["trend"][0] == pytest.approx(10.0)


def test_falling_prices_project_lower():
    closes = [100.0 - 0.5 * i for i in range(40)]
    result = main.predict_future_prices(closes, days=3)
    assert result["slope_per_day"] == pytest.approx(-0.5)
    assert result["predictions"] == sorted(result["predictions"], reverse=True)
    assert result["predictions"][0] < closes[-1]


def test_noisy_prices_fit_worse_than_a_line():
    closes = [50.0 + (5 if i % 2 else -5) for i in range(30)]
    result = main.predict_future_prices(closes)
    assert len(result["predictions"]) == main.FORECAST_DAYS
    assert result["r_squared"] < 0.1


def test_too_little_history_is_rejected():
    with pytest.raises(main.NoDataError, match="at least"):
        main.predict_future_prices([1.0] * (main.MIN_HISTORY_POINTS - 1))


def test_days_must_be_positive():
    with pytest.raises(ValueError):
        main.predict_future_prices([1.0] * 30, days=0)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("aapl", "AAPL"),
        ("  msft ", "MSFT"),
        ("brk-b", "BRK-B"),
        ("BF.B", "BF.B"),
        ("^gspc", "^GSPC"),
        ("EURUSD=X", "EURUSD=X"),
        ("AAPL - Apple Inc", "AAPL"),
    ],
)
def test_normalize_symbol_accepts_tickers(raw, expected):
    assert main.normalize_symbol(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "<script>", "AA PL", "A" * 16, "../etc", "AAPL;rm"])
def test_normalize_symbol_rejects_bad_input(raw):
    with pytest.raises(main.InvalidSymbolError):
        main.normalize_symbol(raw)


def test_fetch_price_history_returns_dated_closes(yahoo):
    calls = yahoo(price_frame([1.0, 2.0, float("nan"), 4.0]))
    history = main.fetch_price_history("AAPL")
    assert calls == ["AAPL"]
    assert [close for _, close in history] == [1.0, 2.0, 4.0]
    assert history[0][0] == date(2026, 1, 2)


def test_fetch_price_history_empty_is_no_data(yahoo):
    yahoo(price_frame([]))
    with pytest.raises(main.NoDataError):
        main.fetch_price_history("NOPE")


def test_fetch_price_history_failure_is_data_source_error(yahoo):
    yahoo(ConnectionError("offline"))
    with pytest.raises(main.DataSourceError):
        main.fetch_price_history("AAPL")


def test_backtest_perfect_line_has_zero_line_error():
    closes = [10.0 + 2 * i for i in range(60)]
    result = main.backtest_line(closes, days=5)
    assert result["line_mae"] == pytest.approx(0.0, abs=1e-6)
    assert result["naive_mae"] > 0
    assert result["line_beat_naive_pct"] == 100.0
    assert result["horizon_days"] == 5


def test_backtest_flat_prices_tie_the_naive_guess():
    result = main.backtest_line([50.0] * 60, days=5)
    assert result["line_mae"] == pytest.approx(0.0, abs=1e-6)
    assert result["naive_mae"] == 0.0
    assert result["line_beat_naive_pct"] == 0.0  # a tie is not a win


def test_backtest_counts_windows():
    # origins 20, 25, ..., while origin + 5 <= 60
    assert main.backtest_line([1.0 + i % 7 for i in range(60)], days=5)["windows"] == 8


def test_backtest_returns_none_when_history_is_too_short():
    assert main.backtest_line([1.0] * 22, days=5) is None


def test_backtest_rejects_bad_arguments():
    with pytest.raises(ValueError):
        main.backtest_line([1.0] * 60, days=0)
    with pytest.raises(ValueError):
        main.backtest_line([1.0] * 60, stride=0)
