# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Security

- Removed the hard-coded Alpha Vantage API key from `main.py` and `static/script.js`. The key committed in 1.0.0 must be treated as compromised and rotated. The server now reads `ALPHA_VANTAGE_API_KEY` from the environment, and the browser only calls this app.

### Fixed

- Predictions always came back empty because current yfinance returns multi-level columns from `download()`. Prices are now read with `Ticker.history`.
- Bad symbols, unknown symbols, short histories and data-source outages return clear messages (400, 404, 502) instead of crashing or failing silently.
- The About and Contact links pointed at routes that did not exist.
- Duplicate `stockSymbol` element id and a footer placed outside `<body>`.

### Added

- Works without an API key; Alpha Vantage is optional and proxied through `/symbol_search`.
- Slope, in-sample R squared and a five-day projection table, plus a chart of the fitted line.
- How it works page and a not-financial-advice notice on every page and in every JSON response.
- Pinned `requirements.txt` and `requirements-dev.txt` for Python 3.11+.
- Offline pytest suite, `scripts/check.sh`, `scripts/dev.sh` and GitHub Actions CI.
- AGENTS.md, CLAUDE.md, CONTRIBUTING.md, SECURITY.md, MIT LICENSE, llms.txt and GitHub templates.

### Removed

- Placeholder Contact page, the unused time-range menu and the 1M/3M/6M fields that were never filled.
- jQuery and jQuery UI (only used for autocomplete; replaced by a native datalist).

## [1.0.0] - 2023-12-11

### Added

- First version: Flask app that takes a stock symbol, shows recent prices from Alpha Vantage and a linear regression projection from yfinance data.

[Unreleased]: https://github.com/patrickking67/stock-predictor/compare/e39fb05...HEAD
[1.0.0]: https://github.com/patrickking67/stock-predictor/commit/e39fb05
