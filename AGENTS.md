# AGENTS.md

Guide for coding agents working in this repo. Keep it accurate when you change commands or layout.

## What this is

An educational Flask app. It fits one straight line (least squares on the day number) through a year of daily closes from Yahoo Finance and extends it five trading days. It is not financial advice and the output is not reliable.

## Stack

- Python 3.11+, Flask 3, yfinance, pandas, numpy, scikit-learn, requests
- Vanilla JS and Chart.js 4.5.1 (jsDelivr, pinned with SRI). No build step, no Node dependencies.
- Tests: pytest. Lint and format: ruff (config in `pyproject.toml`).
- Dependencies are pinned in `requirements.txt` (runtime) and `requirements-dev.txt` (adds pytest, ruff).

## Layout

| Path | Purpose |
| --- | --- |
| `main.py` | All server code: routes, `normalize_symbol`, `fetch_price_history`, `predict_future_prices`, Alpha Vantage helpers |
| `templates/base.html` | Layout, header, disclaimer notice, footer |
| `templates/index.html`, `templates/about.html` | Main page and How it works page |
| `static/script.js` | Form handling, chart, suggestions. Calls only this app's routes |
| `static/style.css` | All styles. Colors are CSS variables at the top |
| `tests/` | Offline pytest suite. `conftest.py` blocks real network calls |
| `scripts/check.sh` | The one check command |
| `scripts/dev.sh` | Dev server on 127.0.0.1:4110 |
| `.claude/launch.json` | Preview config pointing at `scripts/dev.sh`, port 4110 |
| `codeswing.json` | Leftover editor playground config. Unused; leave it |

## Commands

```sh
python3.12 -m venv .venv                      # any Python 3.11+
.venv/bin/pip install -r requirements-dev.txt # install
scripts/dev.sh                                # run: http://127.0.0.1:4110 (PORT overrides)
scripts/check.sh                              # lint + format check + JS syntax + tests
.venv/bin/python -m pytest tests/test_routes.py -k predict   # a subset of tests
.venv/bin/ruff format .                       # fix formatting
```

Preview: start `scripts/dev.sh` (or the `stock-predictor-site` entry in `.claude/launch.json`) and load http://127.0.0.1:4110 . A live prediction needs internet access to Yahoo Finance; the page itself loads offline.

## Conventions

- Keep server logic in `main.py` unless it grows well past its current size.
- Data-source failures raise `DataSourceError`, missing data raises `NoDataError`, bad input raises `InvalidSymbolError`. Routes map them to 502, 404 and 400 with a plain message and the disclaimer.
- Pass query values to `requests` with `params=`, never string formatting. Always set a timeout.
- Front end: set text with `textContent`, never `innerHTML` with data. Keep it dependency free apart from Chart.js.
- Every change to behavior gets a test. Tests must stay offline: mock with the `yahoo` and `alpha_vantage` fixtures.
- Plain, short copy. No em dashes or emojis in committed text.

## Safety rules

- Never commit an API key. `ALPHA_VANTAGE_API_KEY` is read from the environment at request time and must never be sent to the browser or logged. A key was committed in 2023 (commit e39fb05) and has been treated as compromised; do not use or copy anything from that commit.
- Never present output as a recommendation to buy or sell, and never claim accuracy that has not been measured. Keep the disclaimer on every page and in every JSON response.
- Do not add analytics, tracking or new third-party scripts.

## What not to touch

- Git history (no rewrites), GitHub repo settings, branch protection, secrets.
- Do not deploy anywhere.

## How to ship

1. Branch from `main`: `feat/`, `fix/`, `docs/`, `chore/`.
2. Make small Conventional Commits, each passing `scripts/check.sh`.
3. Add a line under `[Unreleased]` in `CHANGELOG.md`.
4. Push and open a PR against `main` using the template. Do not merge it yourself.

## Definition of done

- `scripts/check.sh` passes locally and in CI.
- The change is checked in a browser if it touches templates or static files (375px wide with no horizontal scroll, keyboard focus visible).
- README, AGENTS.md and CHANGELOG.md match the code.
