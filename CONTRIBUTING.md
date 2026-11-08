# Contributing

Thanks for taking a look. This is a small educational project, so changes should keep it simple and honest about what the model can and cannot do.

## Setup

```sh
python3.12 -m venv .venv                      # Python 3.11 or newer
.venv/bin/pip install -r requirements-dev.txt
scripts/dev.sh                                # http://127.0.0.1:4110
```

An Alpha Vantage key is optional. If you use one, export `ALPHA_VANTAGE_API_KEY` in your shell. Never commit it.

## Branches

Branch from `main` with a prefix: `feat/`, `fix/`, `docs/` or `chore/`, for example `fix/empty-history-message`.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`, `ci: ...`, `build: ...`. One logical change per commit, and each commit should pass the checks.

## Checks

```sh
scripts/check.sh
```

Runs ruff lint, ruff format check, a JS syntax check and the offline pytest suite. CI runs the same script.

## Pull request checklist

- [ ] `scripts/check.sh` passes
- [ ] New behavior has tests, and the tests stay offline
- [ ] UI changes checked in a browser, including a 375px wide window
- [ ] No secrets in code, tests, docs or commit messages
- [ ] No output framed as advice to buy or sell, and no unmeasured accuracy claims
- [ ] `CHANGELOG.md` has a line under `[Unreleased]`
