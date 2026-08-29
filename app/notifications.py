"""Email notifications (SMTP when configured, log otherwise).

Per-group opt-out is stored on group_members.notify.
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from flask import current_app

from .db import get_db


def fmt(cents: int) -> str:
    from .algorithms import fmt_cents
    return f"{fmt_cents(abs(cents))} USD"


def notify_expense(group_id: int, expense: dict, actor) -> None:
    _notify_group(
        group_id, actor["id"],
        f"[{actor['name']}] added an expense: {expense['title']} "
        f"({fmt(expense['amount_cents'])})")


def notify_settlement(group_id: int, from_id: int, to_id: int,
                      amount_cents: int, actor) -> None:
    db = get_db()
    frm = db.execute("SELECT name FROM users WHERE id = ?",
                     (from_id,)).fetchone()
    to = db.execute("SELECT name FROM users WHERE id = ?", (to_id,)).fetchone()
    _notify_group(group_id, actor["id"],
                  f"[Settlement] {frm['name']} paid {to['name']} "
                  f"{fmt(amount_cents)}")


def notify_invitation(email: str, group, link: str) -> None:
    _send_email(email, f"Expense Splitter — {group['name']}",
                f"You have been invited to join '{group['name']}'. "
                f"Accept within 72 hours: {link}")


def _notify_group(group_id: int, actor_id: int, message: str) -> None:
    db = get_db()
    group = db.execute("SELECT name FROM groups WHERE id = ?",
                       (group_id,)).fetchone()
    for r in db.execute(
            """SELECT u.email, gm.notify FROM group_members gm
               JOIN users u ON u.id = gm.user_id
               WHERE gm.group_id = ? AND gm.user_id != ?""",
            (group_id, actor_id)):
        if not r["notify"]:  # per-group notification preference
            continue
        _send_email(r["email"], f"Expense Splitter — {group['name']}", message)


def _send_email(to: str, subject: str, body: str) -> None:
    host = os.environ.get("EXPENSE_SPLITTER_SMTP_HOST")
    if not host:
        current_app.logger.info(
            "EMAIL (not sent, no SMTP configured) -> %s: %s | %s",
            to, subject, body)
        return
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, int(os.environ.get(
                "EXPENSE_SPLITTER_SMTP_PORT", "587"))) as smtp:
            smtp.send_message(msg)
    except OSError:
        current_app.logger.warning("Failed to send email to %s", to)
