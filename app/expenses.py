"""Expenses: create, edit, delete with split validation (FR-02..FR-04)."""
from __future__ import annotations

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   url_for)

from .algorithms import SplitValidationError, fmt_cents, validate_split
from .auth import login_required
from .db import get_db
from .helpers import group_required
from .notifications import notify_expense

bp = Blueprint("expenses", __name__)


def _parse_shares(split_type: str, member_ids: list[int]) -> dict[str, int]:
    """Parse the split inputs from the form into per-user raw values."""
    shares: dict[str, int] = {}
    if split_type == "equal":
        selected = request.form.getlist("participants")
        for uid in member_ids:
            shares[str(uid)] = 1 if str(uid) in selected else 0
        if not selected:
            return {}  # everyone participates
        return shares
    if split_type == "percentage":
        for uid in member_ids:
            raw = request.form.get(f"pct_{uid}", "").strip()
            if raw:
                shares[str(uid)] = round(float(raw) * 100)  # percent -> bp
        return shares
    # exact
    for uid in member_ids:
        raw = request.form.get(f"amt_{uid}", "").strip()
        if raw:
            shares[str(uid)] = int(round(float(raw) * 100))
    return shares


def _expense_row(expense_id: int, group_id: int):
    return get_db().execute(
        "SELECT * FROM expenses WHERE id = ? AND group_id = ?",
        (expense_id, group_id)).fetchone()


@bp.route("/groups/<int:group_id>/expenses/new", methods=("GET", "POST"))
@group_required
def new(group_id, group, membership):
    _, members = group_balances_safe(group_id)
    if request.method == "POST":
        title = request.form["title"].strip()
        try:
            amount_cents = int(round(float(request.form["amount"]) * 100))
        except ValueError:
            amount_cents = -1
        split_type = request.form["split_type"]
        if not title or amount_cents <= 0:
            flash("Title and a positive amount are required.")
        else:
            try:
                raw_shares = _parse_shares(split_type, [m["id"] for m in members])
                participant_ids = [str(m["id"]) for m in members]
                split_shares = validate_split(amount_cents, split_type,
                                              raw_shares, participant_ids)
            except (SplitValidationError, ValueError) as e:
                flash(str(e))
            else:
                db = get_db()
                cur = db.execute(
                    """INSERT INTO expenses (group_id, payer_id, title,
                       amount_cents, spent_on, category, notes, split_type,
                       created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (group_id, int(request.form["payer_id"]), title,
                     amount_cents, request.form.get("spent_on") or
                     __import__("datetime").date.today().isoformat(),
                     request.form.get("category", "").strip(),
                     request.form.get("notes", "").strip(),
                     split_type, g.user["id"]))
                for uid, cents in split_shares.items():
                    db.execute(
                        "INSERT INTO expense_shares (expense_id, user_id, "
                        "share_cents) VALUES (?, ?, ?)",
                        (cur.lastrowid, int(uid), cents))
                db.commit()
                notify_expense(group_id, dict(
                    title=title, amount_cents=amount_cents), g.user)
                flash("Expense added.")
                return redirect(url_for("groups.detail", group_id=group_id))
    return render_template("expenses/form.html", group=group, members=members,
                           expense=None, shares={})


@bp.route("/groups/<int:group_id>/expenses/<int:expense_id>/edit",
          methods=("GET", "POST"))
@group_required
def edit(group_id, group, membership, expense_id):
    expense = _expense_row(expense_id, group_id)
    if expense is None:
        from flask import abort
        abort(404)
    _, members = group_balances_safe(group_id)
    db = get_db()
    if request.method == "POST":
        title = request.form["title"].strip()
        try:
            amount_cents = int(round(float(request.form["amount"]) * 100))
        except ValueError:
            amount_cents = -1
        split_type = request.form["split_type"]
        warn_ack = request.form.get("confirm_warning") == "yes"
        has_settlements = db.execute(
            "SELECT COUNT(*) AS n FROM settlements WHERE group_id = ?",
            (group_id,)).fetchone()["n"] > 0
        if not title or amount_cents <= 0:
            flash("Title and a positive amount are required.")
        elif has_settlements and not warn_ack:
            # FR-04: warn before editing a partially-settled expense
            flash("Editing this expense will alter existing settlement "
                  "balances. Check the confirmation box to proceed.")
            return render_template("expenses/form.html", group=group,
                                   members=members, expense=expense,
                                   shares=_shares_of(expense_id),
                                   warn=True)
        else:
            try:
                raw_shares = _parse_shares(split_type, [m["id"] for m in members])
                participant_ids = [str(m["id"]) for m in members]
                split_shares = validate_split(amount_cents, split_type,
                                              raw_shares, participant_ids)
            except (SplitValidationError, ValueError) as e:
                flash(str(e))
            else:
                old_participants = _participants_of(expense_id)
                db.execute(
                    """UPDATE expenses SET payer_id = ?, title = ?,
                       amount_cents = ?, spent_on = ?, category = ?, notes = ?,
                       split_type = ?, updated_at = datetime('now')
                       WHERE id = ?""",
                    (int(request.form["payer_id"]), title, amount_cents,
                     request.form.get("spent_on") or expense["spent_on"],
                     request.form.get("category", "").strip(),
                     request.form.get("notes", "").strip(),
                     split_type, expense_id))
                db.execute("DELETE FROM expense_shares WHERE expense_id = ?",
                           (expense_id,))
                for uid, cents in split_shares.items():
                    db.execute(
                        "INSERT INTO expense_shares (expense_id, user_id, "
                        "share_cents) VALUES (?, ?, ?)",
                        (expense_id, int(uid), cents))
                db.commit()
                new_participants = {int(uid) for uid in split_shares}
                if new_participants != old_participants:
                    flash("Expense participants updated.")
                flash("Expense updated.")
                return redirect(url_for("groups.detail", group_id=group_id))
    return render_template("expenses/form.html", group=group, members=members,
                           expense=expense, shares=_shares_of(expense_id),
                           warn=db.execute(
                               "SELECT COUNT(*) AS n FROM settlements WHERE "
                               "group_id = ?", (group_id,)).fetchone()["n"] > 0)


@bp.route("/groups/<int:group_id>/expenses/<int:expense_id>/delete",
          methods=("POST",))
@group_required
def delete(group_id, group, membership, expense_id):
    expense = _expense_row(expense_id, group_id)
    if expense is None:
        from flask import abort
        abort(404)
    db = get_db()
    has_settlements = db.execute(
        "SELECT COUNT(*) AS n FROM settlements WHERE group_id = ?",
        (group_id,)).fetchone()["n"] > 0
    if has_settlements and request.form.get("confirm_warning") != "yes":
        # FR-04: warning before deleting an expense with recorded settlements
        flash("Deleting this expense will alter existing settlement "
              "balances. Confirm to proceed.")
        return redirect(url_for("groups.detail", group_id=group_id))
    db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()
    flash("Expense deleted.")
    return redirect(url_for("groups.detail", group_id=group_id))


def _shares_of(expense_id: int) -> dict[str, int]:
    rows = get_db().execute(
        "SELECT user_id, share_cents FROM expense_shares WHERE expense_id = ?",
        (expense_id,)).fetchall()
    return {str(r["user_id"]): r["share_cents"] for r in rows}


def _participants_of(expense_id: int) -> set[int]:
    """Return the set of user ids currently participating in the expense."""
    rows = get_db().execute(
        "SELECT user_id FROM expense_shares WHERE expense_id = ? AND share_cents > 0",
        (expense_id,)).fetchall()
    return {r["user_id"] for r in rows}


def group_balances_safe(group_id: int):
    from .helpers import group_balances
    return group_balances(group_id)
