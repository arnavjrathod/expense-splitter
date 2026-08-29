"""Cross-group dashboard (US-11)."""
from __future__ import annotations

from flask import Blueprint, g, render_template

from .auth import login_required
from .db import get_db
from .helpers import group_balances

bp = Blueprint("dashboard", __name__)


@bp.route("/dashboard")
@login_required
def index():
    db = get_db()
    rows = db.execute(
        """SELECT gr.* FROM groups gr
           JOIN group_members gm ON gm.group_id = gr.id
           WHERE gm.user_id = ? ORDER BY gr.name""", (g.user["id"],)).fetchall()
    summary = []
    total = 0
    for grp in rows:
        balances, members = group_balances(grp["id"])
        mine = balances.get(g.user["id"], 0)
        total += mine
        summary.append({
            "group": grp,
            "my_balance": mine,
            "member_count": len(members),
            "is_admin": grp["admin_id"] == g.user["id"],
        })
    return render_template("dashboard.html", summary=summary, total=total)
