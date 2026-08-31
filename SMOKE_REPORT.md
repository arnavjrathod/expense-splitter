# Smoke Report — Code Editor Theme (Expense Splitter)

**Date:** 2026-08-31
**Role:** Smoke tester (no feature changes made; theme change was committed upstream in `3f24868`)

## Scope

Verify the app boots and the happy path works after the "code editor" UI theme
change (`app/static/style.css`, `app/templates/base.html`).

## Environment

- Python 3.11 / Flask, deps via `uv sync` (`.venv` in repo)
- Server: `.venv/bin/python run.py` → http://localhost:5000 (fresh SQLite DB)

## Unit tests

```
.venv/bin/python -m pytest -q
```

**Result: 46 passed, 0 failed. ✅**

## Smoke test (HTTP, live server)

| Step | Request | Result |
|---|---|---|
| Boot server | — | ✅ up, no startup errors |
| Root redirect | `GET /` | ✅ 302 → `/dashboard` |
| Signup page | `GET /signup` | ✅ 200 |
| Signup | `POST /signup` | ✅ 302 → `/dashboard`, session cookie set |
| Dashboard (logged in) | `GET /dashboard` | ✅ 200, contains group name |
| Create group | `POST /groups/new` | ✅ 302 → `/groups/1` |
| Group detail | `GET /groups/1` | ✅ 200 |
| Add expense (equal split) | `POST /groups/1/expenses/new` (`title=Dinner`, `amount=45.00`) | ✅ 302 → group detail; expense visible |
| Settlement page | `GET /groups/1/settlements/new` | ✅ 200 |
| Record settlement | `POST /groups/1/settlements/new` | ✅ 302 |
| Theme live | `GET /static/style.css` served via `base.html` link | ✅ VS Code dark palette (`--bg:#1e1e1e`, `--sidebar:#252526`, syntax tokens `--keyword/--string/--number/--function/--comment`), monospace font stack, `.editor-panel`, `.token-*` classes present |
| Logout | `GET /logout` | ✅ 302 |

## Notes

- One 500 observed during probing was **tester error** (POST missing the
  required `title` form field), not an app bug; retried correctly and passed.
- No code changes were made by this run; only this report is committed.

## Verdict

**PASS** — app boots, all happy-path flows work, and the code-editor theme is
served and referenced by the base template.
