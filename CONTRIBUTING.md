# Contributing

Thanks for helping. Issues and pull requests are welcome in English or Portuguese.

## Setup

    uv sync --all-extras          # Python 3.9+; installs the locked dependencies and dev tools

No uv? `pip install -e ".[sentry]" ruff mypy` works too.

## Before opening a PR

    uv run python -m unittest discover -s tests -t .   # offline: every API is mocked
    uv run ruff check . && uv run ruff format --check .
    uv run mypy

CI runs the same commands on Python 3.9 and 3.12, plus `pip-audit` and a Docker build.

## Ground rules

- **Never hit the real APIs in tests.** Mock `get_json`, `abrir` and the catalog lookups; build images with `tests/ajuda.py`.
- **Changing a detector?** Re-run the matching script in `validacao/` and report the numbers before/after.
- **Be polite to the services.** Keep the pauses between Zooniverse pages and VizieR lookups, and the retry backoff.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`…).
- Note user-visible changes in `CHANGELOG.md`.
