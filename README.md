# Stock Predictor

[![CI](https://github.com/patrickking67/stock-predictor/actions/workflows/ci.yml/badge.svg)](https://github.com/patrickking67/stock-predictor/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A small Flask app that fits one straight line through a year of daily stock prices and extends it five trading days.

> **Educational project, not financial advice. Predictions are not reliable.**
> The "prediction" is a straight line through last year's closing prices. Nothing here is a recommendation to buy or sell, and no accuracy has been measured.

There is no hosted version. It runs locally.

## Features

- Enter a ticker (AAPL, BRK-B, ^GSPC, EURUSD=X) and get a chart of the last year of daily closes with the fitted line continued into a shaded projection zone.
- Shows the slope of the line per trading day, the in-sample R squared, and the line's value for each of the next five trading days.
- Clear messages for bad symbols, unknown symbols, short histories and data-source outages instead of crashes.
- Works without any API key. With an optional Alpha Vantage key on the server it also shows the company name, a latest quote and symbol suggestions. The key never reaches the browser.
- A How it works page that explains the method and its limits.

## How the prediction works

1. Download about one year of daily closing prices (adjusted) from Yahoo Finance with [yfinance](https://github.com/ranaroussi/yfinance).
2. Number the trading days 0, 1, 2, ... and fit `price = a + b * day` by ordinary least squares with scikit-learn's `LinearRegression`.
3. Extend the line five trading days past the last close.

Limits:

- No backtest, no measured accuracy.
- It ignores earnings, news, rates, volatility and the rest of the market. A straight line keeps going forever; prices do not.
- R squared only says how closely last year's prices followed a line. It is measured on the training data and says nothing about forecast accuracy.
- Free data sources can be delayed, wrong, rate limited or down.

## Quickstart

Needs Python 3.11 or newer (CI runs 3.11 and 3.13).

```sh
git clone git@github.com:patrickking67/stock-predictor.git
cd stock-predictor
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
scripts/dev.sh
```

Open http://127.0.0.1:4110 . Set `PORT` to use another port.

Optional: get a free key at https://www.alphavantage.co/support/#api-key and export it before starting the server. Do not commit it.

```sh
export ALPHA_VANTAGE_API_KEY=your-key
scripts/dev.sh
```

`.env.example` lists the variable. The app reads it from the process environment only; it does not load `.env` files.

## Architecture

```
main.py              Flask app: routes, input validation, data fetching, the linear model
templates/           Jinja templates (base.html, index.html, about.html)
static/              style.css, script.js (vanilla JS + Chart.js from jsDelivr), favicon.svg
tests/               pytest suite, fully offline (data sources are mocked)
scripts/check.sh     the one check command (ruff, format check, JS syntax, pytest)
scripts/dev.sh       local dev server on port 4110
```

Routes:

| Route | Returns |
| --- | --- |
| `GET /` | The main page |
| `GET /about` | How it works and limits |
| `GET /predict_stock?symbol=AAPL` | JSON: history, fitted line, five projected values, slope, R squared, notices. 400 bad symbol, 404 no data, 502 data source failed |
| `GET /symbol_search?q=apple` | JSON symbol suggestions proxied from Alpha Vantage. 503 when no key is configured |

## Tests

```sh
scripts/check.sh
```

Runs `ruff check`, `ruff format --check`, `node --check` on the JS (skipped if Node is missing) and `pytest`. The tests never touch the network. CI runs the same script on every push to main and every pull request.

## Deploy

Not deployed. `scripts/dev.sh` uses Flask's development server, which is for local use only.

## License

[MIT](LICENSE). Built by Patrick King in 2023, revised in 2026.
