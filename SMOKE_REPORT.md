# Smoke Test Report — "Change split participants after creation"

**Date:** 2026-08-30
**Scope:** Smoke test only (no new features implemented). Feature under test was
delivered in commit `d14326b` ("Allow changing expense split participants after
creation").

## Environment

- Booted via `uv sync` + `.venv/bin/python run.py` (Flask dev server, port 5000),
  with a throwaway SQLite DB (`EXPENSE_SPLITTER_DB=/tmp/smoke_db/smoke.db`).
- Verified against the running server with `curl` + cookie jars (session auth).

## Unit tests

```
.venv/bin/python -m pytest -q
49 passed in 8.56s
```

Includes the three new tests for this feature (remove participant, add
participant, settlement-warning confirmation path).

## Live happy-path verification

| # | Step | Result |
|---|------|--------|
| 1 | Sign up Alice (`/signup`) | ✅ 302 |
| 2 | Create group "Trip" (`/groups/new`) | ✅ redirects to group detail |
| 3 | Invite Bob, Bob signs up and accepts invite token | ✅ 302, Bob joins group |
| 4 | Add expense: $30.00 equal split, participants = Alice, Bob | ✅ 302, balances show Bob owes Alice **15.00 USD** |
| 5 | Group detail shows participants per expense: `· with Alice, Bob` | ✅ |
| 6 | **Edit expense, remove Bob** (participants = Alice only) | ✅ flash `Expense participants updated.` + `Expense updated.`; detail now shows `· with Alice`; balances recalc to **Everyone is settled up!** |
| 7 | **Edit expense, add Bob back** (participants = Alice, Bob) | ✅ flash `Expense participants updated.`; Bob owes Alice 15.00 USD again |
| 8 | Edit form pre-selects current participants as checkboxes | ✅ (Bob's checkbox `checked`) |
| 9 | Record settlement ($15 Bob → Alice), then edit participants **without** confirm box | ✅ blocked with FR-04 warning "alter existing settlement balances — check the box below to confirm"; no change applied |
| 10 | Same edit **with** `confirm_warning=yes` | ✅ proceeds, expense updated |
| 11 | Exact split: $10.00 paid by Bob (Alice 4.00 / Bob 6.00), then **remove Bob** without adjusting amounts | ✅ correctly rejected: "Exact amounts must total the expense amount (4.00 vs 10.00)" — no partial update |
| 12 | Exact split: remove Bob with `amt_1=10.00` (full amount reassigned) | ✅ `Expense participants updated.`; detail shows `· with Alice`; balances recalc to Alice −10.00 / Bob +10.00 |

## Findings

- **No bugs found.** Participant changes work for equal splits (add/remove) and
  for exact splits when amounts are re-specified to total the expense amount.
- Balances, settlement plan, and the activity feed recalculate correctly after
  every participant change (spot-checked at each step).
- The settlements guard (FR-04) correctly gates participant edits when recorded
  settlements exist, and the confirmation box unblocks the edit.
- Flash message `Expense participants updated.` appears only when the
  participant set actually changed — cosmetic, works as intended.

## Outcome

**SMOKE TEST PASSED.** App boots, happy path verified end-to-end, unit tests
green. Ready for delivery.
