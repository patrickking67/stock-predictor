"""Shared fixtures. Every test runs offline: real network calls fail loudly."""

from __future__ import annotations

import pandas as pd
import pytest

import main


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise main.requests.HTTPError(f"HTTP {self.status_code}")


def price_frame(closes, start="2026-01-02"):
    """A DataFrame shaped like yfinance Ticker.history output."""
    index = pd.bdate_range(start=start, periods=len(closes), tz="America/New_York", name="Date")
    return pd.DataFrame({"Open": closes, "Close": closes, "Volume": [1000] * len(closes)}, index=index)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Remove the API key and block real data sources unless a test mocks them."""
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)

    def no_network(*args, **kwargs):
        raise AssertionError("test tried to reach the network")

    monkeypatch.setattr(main.requests, "get", no_network)
    monkeypatch.setattr(main.yf, "Ticker", no_network)


@pytest.fixture
def client():
    main.app.config.update(TESTING=True)
    return main.app.test_client()


@pytest.fixture
def yahoo(monkeypatch):
    """Call yahoo(frame) or yahoo(exception) to control Ticker.history."""

    calls = []

    def install(result):
        class FakeTicker:
            def __init__(self, symbol):
                calls.append(symbol)

            def history(self, **kwargs):
                if isinstance(result, Exception):
                    raise result
                return result

        monkeypatch.setattr(main.yf, "Ticker", FakeTicker)
        return calls

    return install


@pytest.fixture
def alpha_vantage(monkeypatch):
    """Call alpha_vantage({function: payload}) to answer requests by AV function name."""

    sent = []

    def install(responses, key="test-key"):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", key)

        def fake_get(url, params=None, timeout=None):
            sent.append({"url": url, "params": params, "timeout": timeout})
            result = responses[params["function"]]
            if isinstance(result, main.requests.RequestException):
                raise result
            if isinstance(result, FakeResponse):
                return result
            return FakeResponse(result)

        monkeypatch.setattr(main.requests, "get", fake_get)
        return sent

    return install
