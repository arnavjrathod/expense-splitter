"""Authentication: signup, login, logout, session management."""
from __future__ import annotations

import functools

from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__)


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            "SELECT id, email, name FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def current_user():
    return getattr(g, "user", None)


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return redirect(url_for("auth.login", next=request.path))
        session.permanent = True  # sliding inactivity expiry (FR-08)
        return view(*args, **kwargs)
    return wrapped


@bp.route("/signup", methods=("GET", "POST"))
def signup():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        name = request.form["name"].strip()
        password = request.form["password"]
        error = None
        if not email or "@" not in email:
            error = "A valid email is required."
        elif not name:
            error = "Name is required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        if error is None:
            db = get_db()
            try:
                cur = db.execute(
                    "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
                    (email, name, generate_password_hash(password)))
                db.commit()
            except Exception:
                error = f"Email {email} is already registered."
            else:
                session.clear()
                session["user_id"] = cur.lastrowid
                next_url = request.args.get("next") or url_for("dashboard.index")
                return redirect(next_url)
        flash(error)
    return render_template("auth/signup.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        error = None
        if user is None or not check_password_hash(user["password_hash"], password):
            error = "Incorrect email or password."
        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            session.permanent = True
            next_url = request.args.get("next") or url_for("dashboard.index")
            return redirect(next_url)
        flash(error)
    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
