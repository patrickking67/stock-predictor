"""Stock Predictor: an educational Flask demo.

The "prediction" is a straight line fitted to one year of daily closing prices
(ordinary least squares on the day number) and extended a few trading days
forward. It ignores news, earnings, volatility and everything else that moves
a price. It is not financial advice and the numbers are not reliable.
"""

from __future__ import annotations

import os
import re
from datetime import date, datetime

import numpy as np
import requests
import yfinance as yf
from flask import Flask, jsonify, render_template, request
from sklearn.linear_model import LinearRegression

app = Flask(__name__)

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
HTTP_TIMEOUT_SECONDS = 10
HISTORY_PERIOD = "1y"
FORECAST_DAYS = 5
MIN_HISTORY_POINTS = 20

DISCLAIMER = (
    "Educational project, not financial advice. Predictions are not reliable: "
    "they extend a straight line through last year's closing prices."
)

# Letters, digits and the punctuation Yahoo uses (BRK-B, BF.B, ^GSPC, EURUSD=X).
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9^][A-Z0-9.\-=^]{0,14}$")
SEARCH_PATTERN = re.compile(r"^[A-Za-z0-9 .&'\-]{1,40}$")


class InvalidSymbolError(ValueError):
    """The user sent something that is not a plausible ticker symbol."""


class NoDataError(LookupError):
    """The data source answered but had no usable prices for the symbol."""


class DataSourceError(RuntimeError):
    """The data source could not be reached or refused the request."""


def normalize_symbol(raw: str | None) -> str:
    """Return an upper-case ticker or raise InvalidSymbolError.

    Accepts "aapl", " AAPL ", or an autocomplete label like "AAPL - Apple Inc".
    """
    if raw is None:
        raise InvalidSymbolError("Enter a stock symbol, for example AAPL.")
    symbol = raw.split(" - ")[0].strip().upper()
    if not symbol:
        raise InvalidSymbolError("Enter a stock symbol, for example AAPL.")
    if not SYMBOL_PATTERN.match(symbol):
        raise InvalidSymbolError(
            "That does not look like a ticker symbol. Use letters, digits, '.', '-', '^' or '='."
        )
    return symbol


def alpha_vantage_key() -> str:
    """Read the optional Alpha Vantage key from the environment at call time."""
    return os.environ.get("ALPHA_VANTAGE_API_KEY", "").strip()


def fetch_price_history(symbol: str, period: str = HISTORY_PERIOD) -> list[tuple[date, float]]:
    """Return (date, close) pairs from Yahoo Finance, oldest first."""
    try:
        frame = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
    except Exception as exc:  # yfinance raises many network and parsing errors
        raise DataSourceError("Yahoo Finance could not be reached. Try again in a minute.") from exc
    if frame is None or frame.empty or "Close" not in frame.columns:
        raise NoDataError(f"No price history found for {symbol}. Check the symbol.")
    closes = frame["Close"].dropna()
    return [(_as_date(index), float(value)) for index, value in closes.items()]


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()


def predict_future_prices(closes: list[float], days: int = FORECAST_DAYS) -> dict:
    """Fit a straight line to the closes and extend it `days` steps forward.

    Returns the projected prices, the fitted line over the history, the slope
    per trading day and the in-sample R squared. R squared only says how well a
    line fits the past; it says nothing about forecast accuracy.
    """
    if days < 1:
        raise ValueError("days must be at least 1")
    if len(closes) < MIN_HISTORY_POINTS:
        raise NoDataError(
            f"Only {len(closes)} days of prices are available; at least {MIN_HISTORY_POINTS} are needed."
        )
    y = np.asarray(closes, dtype=float)
    x = np.arange(len(y)).reshape(-1, 1)
    model = LinearRegression().fit(x, y)
    future_x = np.arange(len(y), len(y) + days).reshape(-1, 1)
    return {
        "predictions": [round(float(v), 2) for v in model.predict(future_x)],
        "trend": [round(float(v), 2) for v in model.predict(x)],
        "slope_per_day": round(float(model.coef_[0]), 4),
        "r_squared": round(float(model.score(x, y)), 4),
        "points": len(y),
    }


def alpha_vantage_query(function: str, **params: str) -> dict:
    """Call Alpha Vantage with the server's key. Raise DataSourceError on any failure."""
    key = alpha_vantage_key()
    if not key:
        raise DataSourceError("Alpha Vantage is not configured on this server.")
    try:
        response = requests.get(
            ALPHA_VANTAGE_URL,
            params={"function": function, "apikey": key, **params},
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise DataSourceError("Alpha Vantage could not be reached.") from exc
    if not isinstance(data, dict):
        raise DataSourceError("Alpha Vantage returned an unexpected response.")
    if "Error Message" in data:
        raise DataSourceError("Alpha Vantage did not recognise the request.")
    if "Note" in data or "Information" in data:
        raise DataSourceError("Alpha Vantage rate limit reached. Try again later.")
    return data


def search_symbols(keywords: str) -> list[dict]:
    data = alpha_vantage_query("SYMBOL_SEARCH", keywords=keywords)
    matches = []
    for match in data.get("bestMatches", []):
        symbol = match.get("1. symbol")
        if symbol:
            matches.append({"symbol": symbol, "name": match.get("2. name", "")})
    return matches


def fetch_company_name(symbol: str) -> str | None:
    """Best match name from Alpha Vantage symbol search, preferring an exact symbol."""
    matches = search_symbols(symbol)
    for match in matches:
        if match["symbol"].upper() == symbol:
            return match["name"] or None
    if matches:
        return matches[0]["name"] or None
    return None


def fetch_latest_quote(symbol: str) -> dict | None:
    """Latest price from Alpha Vantage GLOBAL_QUOTE, or None if it has none."""
    quote = alpha_vantage_query("GLOBAL_QUOTE", symbol=symbol).get("Global Quote") or {}
    price = quote.get("05. price")
    if not price:
        return None
    try:
        return {"price": round(float(price), 2), "as_of": quote.get("07. latest trading day")}
    except ValueError:
        return None


def error_response(message: str, status: int):
    return jsonify({"error": message, "disclaimer": DISCLAIMER}), status


@app.route("/")
def index():
    return render_template("index.html", disclaimer=DISCLAIMER, forecast_days=FORECAST_DAYS)


@app.route("/about")
def about():
    return render_template("about.html", disclaimer=DISCLAIMER, forecast_days=FORECAST_DAYS)


@app.route("/symbol_search")
def symbol_search():
    """Server-side proxy so the API key never reaches the browser."""
    keywords = request.args.get("q", "").strip()
    if not SEARCH_PATTERN.match(keywords):
        return jsonify({"matches": [], "error": "Search needs 1 to 40 letters or digits."}), 400
    if not alpha_vantage_key():
        return jsonify({"matches": [], "error": "Symbol search is not configured."}), 503
    try:
        return jsonify({"matches": search_symbols(keywords)})
    except DataSourceError as exc:
        return jsonify({"matches": [], "error": str(exc)}), 502


@app.route("/predict_stock")
def predict_stock():
    try:
        symbol = normalize_symbol(request.args.get("symbol"))
        history = fetch_price_history(symbol)
        model = predict_future_prices([close for _, close in history])
    except InvalidSymbolError as exc:
        return error_response(str(exc), 400)
    except NoDataError as exc:
        return error_response(str(exc), 404)
    except DataSourceError as exc:
        return error_response(str(exc), 502)
    except Exception:
        app.logger.exception("Unexpected error predicting %r", request.args.get("symbol"))
        return error_response("Something went wrong on the server.", 500)

    notices = []
    company_name = None
    last_date, last_close = history[-1]
    latest = {"price": round(last_close, 2), "as_of": last_date.isoformat(), "source": "Yahoo Finance close"}
    if alpha_vantage_key():
        try:
            company_name = fetch_company_name(symbol)
            quote = fetch_latest_quote(symbol)
            if quote:
                latest = {**quote, "source": "Alpha Vantage quote"}
        except DataSourceError as exc:
            notices.append(f"{exc} Showing Yahoo Finance data only.")
    else:
        notices.append(
            "Company names and live quotes need ALPHA_VANTAGE_API_KEY on the server; "
            "showing the last Yahoo Finance close."
        )

    return jsonify(
        {
            "symbol": symbol,
            "company_name": company_name,
            "latest": latest,
            "history": [{"date": d.isoformat(), "close": round(c, 2)} for d, c in history],
            "trend": model["trend"],
            "predictions": model["predictions"],
            "model": {
                "method": "Straight line (least squares) through daily closes",
                "period": HISTORY_PERIOD,
                "points": model["points"],
                "slope_per_day": model["slope_per_day"],
                "r_squared": model["r_squared"],
            },
            "notices": notices,
            "disclaimer": DISCLAIMER,
        }
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "4110")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
