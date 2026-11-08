# Security policy

## Supported versions

Only the latest commit on `main` is supported. There are no maintained releases.

## Reporting a vulnerability

Report privately through GitHub: https://github.com/patrickking67/stock-predictor/security/advisories/new

Please do not open a public issue for security problems, and do not include real API keys in reports.

## Scope

In scope: the Flask app in this repo (`main.py`, templates, static files), including input handling, the `/predict_stock` and `/symbol_search` routes, and anything that could expose the server's `ALPHA_VANTAGE_API_KEY`.

Out of scope: Yahoo Finance, Alpha Vantage, jsDelivr and Google Fonts themselves, and the accuracy of predictions (the app makes no accuracy claims).

## What to expect

This is a personal project maintained in spare time. Expect an acknowledgement within 7 days and a fix or a decision within 30 days for confirmed issues.

## Known history

An Alpha Vantage key was committed in 2023 (commit e39fb05). It has been removed from the code and must be treated as compromised.
