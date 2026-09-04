# Smoke Test Report — Theme Switcher (light / neon dark mode)

**Date:** 2026-09-04
**Scope:** Verify the previously implemented theme switcher (commit `6c1ea94`) boots and works end-to-end. No new features implemented.
**Result: PASS** ✅

## Environment

- Python 3.11, Flask, managed with `uv` (`uv sync` succeeded; `.venv` in-repo)
- App booted via `.venv/bin/python run.py` on `http://localhost:5000`

## Unit tests

```
.venv/bin/python -m pytest -q
47 passed in 4.11s
```

Includes the `TestThemeSwitcher` suite: toggle button present, neon CSS vars
loaded, theme JS loaded, inline default-theme bootstrap present.

## Smoke test (HTTP, against running server)

| Step | Check | Result |
|---|---|---|
| 1 | `GET /` redirects unauthenticated user | 302 ✅ |
| 2 | Signup page renders with `#theme-toggle` in layout | present ✅ |
| 3 | Signup POST → redirect to `/dashboard` | 302 ✅ |
| 4 | `/dashboard` renders 200 with theme toggle + `data-theme` inline bootstrap script | ✅ |
| 5 | `GET /static/style.css` → 200; contains `:root` light vars and `[data-theme="neon"]` overrides | ✅ |
| 6 | `GET /static/app.js` → 200; contains localStorage persistence, toggle handler, `aria-pressed` + label update (`⚡ Neon` / `☀ Light`) | ✅ |
| 7 | Create group (`POST /groups/new`) → 302; group appears in list & dashboard | ✅ |
| 8 | Add expense (`POST /groups/1/expenses/new`, equal split) → 302; expense shows on group detail with Balances | ✅ |
| 9 | `base.html` inline `<script>` sets `data-theme` before first paint (no flash-of-wrong-theme) | ✅ |

## Notes

- Two initial 4xx/5xx responses during smoke testing were **tester error**
  (wrong endpoint `/groups` instead of `/groups/new`; wrong form field names).
  Correcting to the app's actual routes/fields resolved them — not app bugs.
- Theme behavior verified at HTTP level (markup, CSS vars, JS logic). Actual
  click-toggle visual behavior is client-side JS covered by app.js inspection
  and unit tests; localStorage persistence logic confirmed in source.
- Server stopped cleanly; test DB and cookies cleaned up.