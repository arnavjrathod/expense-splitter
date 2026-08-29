"""Core money math: splits, balances, and debt simplification.

All amounts are integer cents to avoid floating point issues.
"""
from __future__ import annotations


class SplitValidationError(ValueError):
    """Raised when a split does not add up to the expense total."""


def validate_split(amount_cents: int, split_type: str, shares: dict[str, int],
                   participant_ids: list[str]) -> dict[str, int]:
    """Validate a split and return per-user share amounts in cents.

    shares semantics by split_type:
      - "equal": shares maps user_id -> 1/0 (included flag). Every user in
        participant_ids with a truthy flag participates; if the dict is empty,
        all participants participate.
      - "percentage": shares maps user_id -> percent * 100 (basis points, i.e.
        25.5% -> 2550). Must total exactly 10000 bp.
      - "exact": shares maps user_id -> amount in cents. Must total the
        expense amount.
    """
    if amount_cents <= 0:
        raise SplitValidationError("Expense amount must be positive.")
    if split_type not in ("equal", "percentage", "exact"):
        raise SplitValidationError("Unknown split type.")
    if not participant_ids:
        raise SplitValidationError("An expense needs at least one participant.")

    if split_type == "equal":
        included = [u for u in participant_ids if shares.get(u, 0 if shares else 1)]
        if not shares:
            included = list(participant_ids)
        if not included:
            raise SplitValidationError("Select at least one member to split with.")
        return split_equal(amount_cents, included)

    if set(shares.keys()) - set(participant_ids):
        raise SplitValidationError("Split includes non-participants.")

    if split_type == "percentage":
        total_bp = sum(shares.values())
        if total_bp != 10000:
            raise SplitValidationError(
                f"Percentages must total 100% (currently {total_bp / 100:.2f}%).")
        return {u: round(amount_cents * bp / 10000) for u, bp in shares.items()}

    # exact
    total = sum(shares.values())
    if total != amount_cents:
        raise SplitValidationError(
            f"Exact amounts must total the expense amount "
            f"({fmt_cents(total)} vs {fmt_cents(amount_cents)}).")
    return dict(shares)


def split_equal(amount_cents: int, member_ids: list[str]) -> dict[str, int]:
    """Split evenly, distributing leftover cents to the first members."""
    n = len(member_ids)
    base = amount_cents // n
    remainder = amount_cents - base * n
    return {u: base + (1 if i < remainder else 0)
            for i, u in enumerate(member_ids)}


def fmt_cents(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def compute_balances(expenses: list[dict], settlements: list[dict]) -> dict[str, int]:
    """Return user_id -> balance in cents for a group.

    balance = (amount paid for others) - (amount owed) + (received in settlements)
    Positive means the member is owed money; negative means they owe.
    """
    users: set[str] = set()
    for e in expenses:
        users.add(e["payer_id"])
        users.update(e["shares"])
    for s in settlements:
        users.add(s["from_id"])
        users.add(s["to_id"])
    balances: dict[str, int] = {u: 0 for u in users}
    for e in expenses:
        balances[e["payer_id"]] += e["amount_cents"]
        for uid, share in e["shares"].items():
            balances[uid] -= share
    for s in settlements:
        balances[s["from_id"]] += s["amount_cents"]
        balances[s["to_id"]] -= s["amount_cents"]
    return balances


def simplify_debts(balances: dict[str, int]) -> list[dict]:
    """Greedy debt simplification: minimum-transaction settlement plan.

    Returns a list of {from_id, to_id, amount_cents} transfers.
    """
    creditors = [(u, b) for u, b in balances.items() if b > 0]
    debtors = [(u, -b) for u, b in balances.items() if b < 0]
    # Largest first keeps the transaction count minimal for typical inputs.
    creditors.sort(key=lambda x: -x[1])
    debtors.sort(key=lambda x: -x[1])
    ci = di = 0
    transfers = []
    while ci < len(creditors) and di < len(debtors):
        cu, camt = creditors[ci]
        du, damt = debtors[di]
        amt = min(camt, damt)
        if amt > 0:
            transfers.append({"from_id": du, "to_id": cu, "amount_cents": amt})
        creditors[ci] = (cu, camt - amt)
        debtors[di] = (du, damt - amt)
        if creditors[ci][1] == 0:
            ci += 1
        if debtors[di][1] == 0:
            di += 1
    return transfers
