"""Groups: create, manage members, invitations, deletion."""
from __future__ import annotations

from flask import (Blueprint, flash, g, redirect, render_template,
                   request, url_for)
from werkzeug.security import generate_password_hash

from .auth import login_required
from .db import get_db
from .helpers import (admin_required, create_invitation, get_membership,
                      group_balances, group_required, invitation_valid)

bp = Blueprint("groups", __name__)


@bp.route("/groups")
@login_required
def list_groups():
    groups = get_db().execute(
        """SELECT gr.*, (SELECT COUNT(*) FROM group_members gm
                         WHERE gm.group_id = gr.id) AS member_count
           FROM groups gr
           JOIN group_members gm ON gm.group_id = gr.id
           WHERE gm.user_id = ? ORDER BY gr.created_at DESC""",
        (g.user["id"],)).fetchall()
    return render_template("groups/list.html", groups=groups)


@bp.route("/groups/new", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        name = request.form["name"].strip()
        description = request.form.get("description", "").strip()
        currency = request.form.get("currency", "USD").strip() or "USD"
        if not name:
            flash("Group name is required.")
        else:
            db = get_db()
            cur = db.execute(
                "INSERT INTO groups (name, description, currency, admin_id) "
                "VALUES (?, ?, ?, ?)", (name, description, currency, g.user["id"]))
            db.execute(
                "INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
                (cur.lastrowid, g.user["id"]))
            db.commit()
            flash(f"Group '{name}' created.")
            return redirect(url_for("groups.detail", group_id=cur.lastrowid))
    return render_template("groups/create.html")


@bp.route("/groups/<int:group_id>")
@group_required
def detail(group_id, group, membership):
    balances, members = group_balances(group_id)
    from .algorithms import simplify_debts
    plan = simplify_debts(balances)
    db = get_db()
    expenses = db.execute(
        """SELECT e.*, u.name AS payer_name FROM expenses e
           JOIN users u ON u.id = e.payer_id
           WHERE e.group_id = ? ORDER BY e.spent_on DESC, e.id DESC""",
        (group_id,)).fetchall()
    settlements = db.execute(
        """SELECT s.*, uf.name AS from_name, ut.name AS to_name
           FROM settlements s JOIN users uf ON uf.id = s.from_id
           JOIN users ut ON ut.id = s.to_id
           WHERE s.group_id = ? ORDER BY s.paid_on DESC, s.id DESC""",
        (group_id,)).fetchall()
    member_by_id = {m["id"]: m for m in members}
    expense_participants = {
        e["id"]: [member_by_id[uid["user_id"]]["name"]
                  for uid in db.execute(
                      "SELECT user_id FROM expense_shares "
                      "WHERE expense_id = ? AND share_cents > 0",
                      (e["id"],)).fetchall()
                  if uid["user_id"] in member_by_id]
        for e in expenses
    }
    return render_template(
        "groups/detail.html", group=group, members=members,
        member_by_id=member_by_id, balances=balances, plan=plan,
        expenses=expenses, settlements=settlements,
        expense_participants=expense_participants,
        is_admin=group["admin_id"] == g.user["id"],
        has_settlements=len(settlements) > 0)


@bp.route("/groups/<int:group_id>/invite", methods=("POST",))
@group_required
def invite(group_id, group, membership):
    email = request.form["email"].strip().lower()
    if not email or "@" not in email:
        flash("Enter a valid email to invite.")
        return redirect(url_for("groups.detail", group_id=group_id))
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing and get_membership(group_id, existing["id"]):
        flash("That user is already a member.")
        return redirect(url_for("groups.detail", group_id=group_id))
    token = create_invitation(group_id, email, g.user["id"])
    link = url_for("groups.accept_invite", token=token, _external=True)
    # FR-01: non-existing users are directed to sign up first (the link
    # itself carries them to signup -> accept).
    from .notifications import notify_invitation
    notify_invitation(email, group, link)
    flash(f"Invitation sent to {email} (valid for 72 hours). Link: {link}")
    return redirect(url_for("groups.detail", group_id=group_id))


@bp.route("/invite/<token>", methods=("GET", "POST"))
def accept_invite(token):
    db = get_db()
    inv = db.execute("SELECT * FROM invitations WHERE token = ?", (token,)).fetchone()
    if not invitation_valid(inv):
        abort(404, description="This invitation is invalid or expired.")
    group = get_db().execute("SELECT * FROM groups WHERE id = ?",
                             (inv["group_id"],)).fetchone()
    # Sign up flow for users without an account (FR-01)
    if g.user is None:
        return render_template("groups/accept_signup.html",
                               token=token, group=group, email=inv["email"])
    return _accept(db, inv, g.user)


def _accept(db, inv, user):
    if user["email"].lower() != inv["email"]:
        flash(f"This invitation was sent to {inv['email']}. "
              f"Please log in as that user to accept it.")
        return redirect(url_for("dashboard.index"))
    db.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
               (inv["group_id"], user["id"]))
    db.execute(
        "UPDATE invitations SET accepted_at = datetime('now'), accepted_user_id = ? "
        "WHERE id = ?", (user["id"], inv["id"]))
    db.commit()
    group = db.execute("SELECT name FROM groups WHERE id = ?",
                       (inv["group_id"],)).fetchone()
    flash(f"You joined '{group['name']}'!")
    return redirect(url_for("groups.detail", group_id=inv["group_id"]))


@bp.route("/invite/<token>/signup", methods=("POST",))
def accept_invite_signup(token):
    """Create an account from an invitation link and join the group."""
    db = get_db()
    inv = db.execute("SELECT * FROM invitations WHERE token = ?", (token,)).fetchone()
    if not invitation_valid(inv):
        abort(404, description="This invitation is invalid or expired.")
    name = request.form["name"].strip()
    password = request.form["password"]
    if not name or len(password) < 6:
        flash("Name is required and password must be at least 6 characters.")
        return redirect(url_for("groups.accept_invite", token=token))
    cur = db.execute(
        "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
        (inv["email"], name, generate_password_hash(password)))
    session_user = cur.lastrowid
    db.commit()
    from flask import session
    session.clear()
    session["user_id"] = session_user
    user = db.execute("SELECT * FROM users WHERE id = ?", (session_user,)).fetchone()
    return _accept(db, inv, user)


@bp.route("/groups/<int:group_id>/members/<int:user_id>/remove", methods=("POST",))
@admin_required
def remove_member(group_id, group, user_id):
    # FR-06: cannot remove a member with a non-zero balance
    balances, _ = group_balances(group_id)
    if balances.get(user_id, 0) != 0:
        flash("This member still has an outstanding balance and cannot be "
              "removed until it is settled.")
        return redirect(url_for("groups.detail", group_id=group_id))
    db = get_db()
    member = db.execute(
        "SELECT u.name FROM users u WHERE u.id = ?", (user_id,)).fetchone()
    db.execute("DELETE FROM group_members WHERE group_id = ? AND user_id = ?",
               (group_id, user_id))
    db.execute("UPDATE group_members SET notify = 0 WHERE group_id = ? "
               "AND user_id = ?", (group_id, user_id))
    db.commit()
    flash(f"Removed {member['name'] if member else 'member'} from the group.")
    return redirect(url_for("groups.detail", group_id=group_id))


@bp.route("/groups/<int:group_id>/delete", methods=("POST",))
@admin_required
def delete(group_id, group):
    # FR-07: only when all balances are zero; admin confirmed via UI form.
    balances, _ = group_balances(group_id)
    if any(b != 0 for b in balances.values()):
        flash("All balances must be zero before the group can be deleted.")
        return redirect(url_for("groups.detail", group_id=group_id))
    if request.form.get("confirm") != group["name"]:
        flash("Type the group name exactly to confirm deletion.")
        return redirect(url_for("groups.detail", group_id=group_id))
    db = get_db()
    db.execute("DELETE FROM groups WHERE id = ?", (group_id,))
    db.commit()
    flash(f"Group '{group['name']}' deleted.")
    return redirect(url_for("groups.list_groups"))


@bp.route("/groups/<int:group_id>/edit", methods=("GET", "POST"))
@admin_required
def edit(group_id, group):
    if request.method == "POST":
        name = request.form["name"].strip()
        if not name:
            flash("Group name is required.")
        else:
            db = get_db()
            db.execute(
                "UPDATE groups SET name = ?, description = ?, currency = ? "
                "WHERE id = ?",
                (name, request.form.get("description", "").strip(),
                 request.form.get("currency", "USD").strip() or "USD", group_id))
            db.commit()
            flash("Group updated.")
            return redirect(url_for("groups.detail", group_id=group_id))
    return render_template("groups/edit.html", group=group)
