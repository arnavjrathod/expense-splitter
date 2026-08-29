"""Shared helpers for group membership and security checks."""
from __future__ import annotations

import functools
import secrets
from datetime import datetime, timedelta

from flask import abort, flash, g, render_template, request, url_for

from .db import get_db
from .auth import login_required


def get_membership(group_id: int, user_id: int):
    return get_db().execute(
        "SELECT * FROM group_members WHERE group_id = ? AND user_id = ?",
        (group_id, user_id)).fetchone()


def get_group(group_id: int):
    return get_db().execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()


def group_required(view):
    """Only members of the group may access the view (Security NFR)."""
    @login_required
    @functools.wraps(view)
    def wrapped(group_id, *args, **kwargs):
        group = get_group(group_id)
        if group is None:
            abort(404)
        membership = get_membership(group_id, g.user["id"])
        if membership is None:
            abort(403)
        return view(group_id, group=group, membership=membership, *args, **kwargs)
    return wrapped


def admin_required(view):
    @group_required
    @functools.wraps(view)
    def wrapped(group_id, group, membership, **kwargs):
        if group["admin_id"] != g.user["id"]:
            abort(403)
        return view(group_id, group=group, **kwargs)
    return wrapped


def group_balances(group_id: int):
    """Return (balances: dict user_id -> cents, member_rows)."""
    db = get_db()
    expenses = []
    for e in db.execute(
            "SELECT * FROM expenses WHERE group_id = ?", (group_id,)):
        shares = {r["user_id"]: r["share_cents"] for r in db.execute(
            "SELECT user_id, share_cents FROM expense_shares WHERE expense_id = ?",
            (e["id"],))}
        expenses.append({**dict(e), "shares": shares})
    settlements = [dict(r) for r in db.execute(
        "SELECT * FROM settlements WHERE group_id = ?", (group_id,))]
    from .algorithms import compute_balances
    balances = compute_balances(expenses, settlements)
    members = db.execute(
        """SELECT u.id, u.email, u.name FROM group_members gm
           JOIN users u ON u.id = gm.user_id WHERE gm.group_id = ?
           ORDER BY u.name""", (group_id,)).fetchall()
    for m in members:
        balances.setdefault(m["id"], 0)
    return balances, members


def invitation_valid(inv) -> bool:
    if inv is None or inv["accepted_at"] is not None:
        return False
    expires = datetime.fromisoformat(inv["expires_at"])
    return datetime.utcnow() <= expires


def create_invitation(group_id: int, email: str, invited_by: int):
    db = get_db()
    token = secrets.token_urlsafe(24)
    expires = (datetime.utcnow() + timedelta(hours=72)).isoformat()  # FR-01
    db.execute(
        """INSERT INTO invitations (group_id, email, token, invited_by, expires_at)
           VALUES (?, ?, ?, ?, ?)""",
        (group_id, email.lower(), token, invited_by, expires))
    db.commit()
    return token


def error_page(message: str, code: int = 400):
    return render_template("error.html", message=message), code
