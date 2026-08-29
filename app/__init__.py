"""Application factory."""
from __future__ import annotations

import os
from datetime import timedelta

from flask import Flask

from .db import get_db, close_db, init_db


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("EXPENSE_SPLITTER_SECRET", "dev-secret-change-me")
    # FR-08: sessions expire after a configurable period of inactivity.
    app.permanent_session_lifetime = timedelta(
        minutes=int(os.environ.get("EXPENSE_SPLITTER_SESSION_MINUTES", "120")))

    if test_config:
        app.config.update(test_config)

    init_db()
    app.teardown_appcontext(close_db)

    from .auth import bp as auth_bp
    from .groups import bp as groups_bp
    from .expenses import bp as expenses_bp
    from .settlements import bp as settlements_bp
    from .dashboard import bp as dashboard_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(settlements_bp)
    app.register_blueprint(dashboard_bp)

    from .auth import login_required, current_user

    @app.route("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("dashboard.index"))

    @app.context_processor
    def inject_user():
        return {"current_user": current_user()}

    @app.template_filter("initials")
    def initials(name):
        """First letters of the first two words, uppercased ("Ada L" -> "AL")."""
        parts = (name or "?").split()
        return ("".join(p[0] for p in parts[:2]) or "?").upper()

    @app.template_filter("money")
    def money(cents):
        from .algorithms import fmt_cents
        sign = "-" if cents < 0 else ""
        return f"{sign}{fmt_cents(abs(cents))}"

    @app.context_processor
    def inject_helpers():
        return {"login_required": login_required}

    return app
