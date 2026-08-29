"""Settlement views."""
from __future__ import annotations

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .db import get_db
from .helpers import group_balances, group_required
from .notifications import notify_settlement

bp = Blueprint("settlements", __name__)


@bp.route("/groups/<int:group_id>/settlements/new", methods=("GET", "POST"))
@group_required
def new(group_id, group, membership):
    balances, members = group_balances(group_id)
    if request.method == "POST":
        try:
            from_id = int(request.form["from_id"])
            to_id = int(request.form["to_id"])
            amount_cents = int(round(float(request.form["amount"]) * 100))
        except (KeyError, ValueError):
            flash("Choose a payer, a recipient, and a positive amount.")
            return redirect(url_for("settlements.new", group_id=group_id))
        if from_id == to_id:
            flash("Payer and recipient must be different members.")
        elif amount_cents <= 0:
            flash("Amount must be positive.")
        elif from_id not in [m["id"] for m in members] or \
                to_id not in [m["id"] for m in members]:
            flash("Both members must belong to this group.")
        else:
            db = get_db()
            db.execute(
                """INSERT INTO settlements (group_id, from_id, to_id,
                   amount_cents, paid_on, note, created_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (group_id, from_id, to_id, amount_cents,
                 request.form.get("paid_on") or
                 __import__("datetime").date.today().isoformat(),
                 request.form.get("note", "").strip(), g.user["id"]))
            db.commit()  # FR-03: balances recalc immediately on next read
            notify_settlement(group_id, from_id, to_id, amount_cents, g.user)
            flash("Settlement recorded.")
            return redirect(url_for("groups.detail", group_id=group_id))
    return render_template("settlements/new.html", group=group,
                           members=members, balances=balances)


@bp.route("/groups/<int:group_id>/settlements/<int:settlement_id>/delete",
          methods=("POST",))
@group_required
def delete(group_id, group, membership, settlement_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM settlements WHERE id = ? AND group_id = ?",
        (settlement_id, group_id)).fetchone()
    if row is None:
        from flask import abort
        abort(404)
    db.execute("DELETE FROM settlements WHERE id = ?", (settlement_id,))
    db.commit()
    flash("Settlement removed.")
    return redirect(url_for("groups.detail", group_id=group_id))


@bp.route("/groups/<int:group_id>/notifications/toggle", methods=("POST",))
@group_required
def toggle_notifications(group_id, group, membership):
    db = get_db()
    db.execute(
        "UPDATE group_members SET notify = 1 - notify "
        "WHERE group_id = ? AND user_id = ?", (group_id, g.user["id"]))
    db.commit()
    row = db.execute(
        "SELECT notify FROM group_members WHERE group_id = ? AND user_id = ?",
        (group_id, g.user["id"])).fetchone()
    flash("Email notifications for this group are now "
          + ("on." if row["notify"] else "off."))
    return redirect(url_for("groups.detail", group_id=group_id))
