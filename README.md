# Expense Splitter

A web application for groups — friends, roommates, travel companions — to track
shared expenses and settle up with the minimum number of transactions.

## Features

- Groups with email invitations (72-hour validity; sign-up-on-accept flow)
- Expenses with equal / percentage / exact-amount splits and real-time
  split validation
- Live balances and a minimal-transaction settlement plan (debt simplification)
- Settlement recording and a combined activity feed
- Cross-group balance dashboard
- Email notifications (SMTP optional; logged otherwise) with per-group opt-out
- Session-based auth with configurable inactivity expiry

## Stack

Python 3.11+, Flask, SQLite (integer cents for all money math), Jinja2
templates, vanilla JS. Managed with [uv](https://docs.astral.sh/uv/); the
`.venv` lives inside the repo for portability.

## Setup & Run

```sh
uv sync                 # creates .venv and installs dependencies
.venv/bin/python run.py # serves on http://localhost:5000
```

Environment variables (all optional):

| Variable | Default | Purpose |
|---|---|---|
| `EXPENSE_SPLITTER_DB` | `data/expenses.db` | SQLite path |
| `EXPENSE_SPLITTER_SECRET` | dev value | Session secret (set in production!) |
| `EXPENSE_SPLITTER_SESSION_MINUTES` | `120` | Session inactivity timeout |
| `EXPENSE_SPLITTER_SMTP_HOST` / `_PORT` | unset | Send real email when set |

## Tests

```sh
.venv/bin/python -m pytest -q
```
