"""Integration tests through the Flask app covering the FRs and security."""
import re

import pytest

from app import create_app
from app.db import init_db

ADMIN_EMAIL = "a@x.com"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("EXPENSE_SPLITTER_DB", str(tmp_path / "test.db"))
    init_db(str(tmp_path / "test.db"))
    app = create_app({"TESTING": True, "SECRET_KEY": "test"})
    with app.test_client() as c:
        yield c


def signup(client, email, name, password="secret123"):
    return client.post("/signup", data={"email": email, "name": name,
                                        "password": password})


def login(client, email, password="secret123"):
    return client.post("/login", data={"email": email, "password": password})


def logout(client):
    return client.get("/logout")


def make_group(client, name="Trip"):
    """Create a group; return its id parsed from the redirect target."""
    rv = client.post("/groups/new", data={"name": name, "description": "",
                                          "currency": "USD"})
    assert rv.status_code == 302
    return int(re.search(r"/groups/(\d+)", rv.headers["Location"]).group(1))


def invite_email(client, gid, email):
    rv = client.post(f"/groups/{gid}/invite", data={"email": email},
                     follow_redirects=True)
    m = re.search(r"/invite/([A-Za-z0-9_\-]+)", rv.get_data(as_text=True))
    assert m, f"no invitation link in response: {rv.get_data(as_text=True)[:400]}"
    return m.group(1)


def add_member(client, gid, email, name):
    """Admin invites email; the user joins (signing up if new); back to admin."""
    token = invite_email(client, gid, email)
    logout(client)
    rv = signup(client, email, name)
    if rv.status_code == 200:  # already registered -> log in instead
        login(client, email)
    rv = client.get(f"/invite/{token}")
    assert rv.status_code == 302  # joined
    logout(client)
    login(client, ADMIN_EMAIL)


def add_expense(client, gid, title="Dinner", amount="30.00", payer="1",
                split_type="equal", extra=None):
    data = {"title": title, "amount": amount, "payer_id": payer,
            "split_type": split_type, "spent_on": "2025-01-15"}
    if extra:
        data.update(extra)
    return client.post(f"/groups/{gid}/expenses/new", data=data)


def record_settlement(client, gid, from_id, to_id, amount, paid_on="2025-01-16"):
    return client.post(f"/groups/{gid}/settlements/new",
                       data={"from_id": from_id, "to_id": to_id,
                             "amount": amount, "paid_on": paid_on})


class TestThemeSwitcher:
    def test_theme_toggle_button_present(self, client):
        rv = client.get("/login")
        assert rv.status_code == 200
        html = rv.get_data(as_text=True)
        assert 'id="theme-toggle"' in html
        assert 'theme-toggle' in html

    def test_theme_css_loaded(self, client):
        rv = client.get("/static/style.css")
        assert rv.status_code == 200
        css = rv.get_data(as_text=True)
        assert "[data-theme=\"neon\"]" in css
        assert "--bg:" in css
        assert "--accent:" in css

    def test_theme_js_loaded(self, client):
        rv = client.get("/static/app.js")
        assert rv.status_code == 200
        js = rv.get_data(as_text=True)
        assert "localStorage.getItem('theme')" in js
        assert "data-theme" in js

    def test_theme_default_set_inline(self, client):
        rv = client.get("/login")
        html = rv.get_data(as_text=True)
        assert "document.documentElement.setAttribute('data-theme', theme)" in html
        assert "localStorage.getItem('theme')" in html




class TestGroups:
    def test_create_group(self, client):
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        assert b"created" in client.get("/groups").data
        assert client.get(f"/groups/{gid}").status_code == 200

    def test_security_non_member_cannot_view(self, client):
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        logout(client)
        signup(client, "b@x.com", "Bob")
        rv = client.get(f"/groups/{gid}")
        assert rv.status_code == 403

    def test_invitation_flow_signup(self, client):
        # FR-01: invited user without an account signs up and joins
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        token = invite_email(client, gid, "bob@x.com")
        logout(client)
        rv = client.get(f"/invite/{token}")
        assert b"invited" in rv.data
        rv = client.post(f"/invite/{token}/signup",
                         data={"name": "Bob", "password": "secret123"})
        assert rv.status_code == 302
        rv = client.get(f"/groups/{gid}")
        assert b"Bob" in rv.data

    def test_expired_or_reused_invitation_rejected(self, client):
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        token = invite_email(client, gid, "bob@x.com")
        # alice (wrong email) cannot accept
        rv = client.get(f"/invite/{token}", follow_redirects=True)
        assert b"Please log in as that user" in rv.data

    def test_member_removal_blocked_with_balance(self, client):
        # FR-06
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_member(client, gid, "b@x.com", "Bob")
        add_expense(client, gid, amount="30.00")  # alice paid for all
        # bob now owes; alice (admin) cannot remove him
        rv = client.post(f"/groups/{gid}/members/2/remove",
                         follow_redirects=True)
        assert b"cannot be removed" in rv.data
        # after bob settles, removal works
        record_settlement(client, gid, from_id=2, to_id=1, amount="15.00")
        rv = client.post(f"/groups/{gid}/members/2/remove",
                         follow_redirects=True)
        assert b"Removed" in rv.data

    def test_group_deletion_blocked_with_balances(self, client):
        # FR-07
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_member(client, gid, "b@x.com", "Bob")
        add_expense(client, gid, amount="30.00")  # alice owed 15
        rv = client.post(f"/groups/{gid}/delete", data={"confirm": "Trip"},
                         follow_redirects=True)
        assert b"balances must be zero" in rv.data
        rv = client.get(f"/groups/{gid}")
        assert rv.status_code == 200  # group still exists

    def test_group_deletion_requires_exact_confirmation(self, client):
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        rv = client.post(f"/groups/{gid}/delete", data={"confirm": "wrong"},
                         follow_redirects=True)
        assert b"Type the group name" in rv.data
        assert client.get(f"/groups/{gid}").status_code == 200

    def test_group_deletion_after_settling(self, client):
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        # single member: expense paid by self -> balance zero
        add_expense(client, gid, amount="30.00")
        rv = client.post(f"/groups/{gid}/delete", data={"confirm": "Trip"},
                         follow_redirects=True)
        assert b"deleted" in rv.data
        assert client.get(f"/groups/{gid}").status_code == 404


class TestExpenses:
    def test_add_equal_expense(self, client):
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_expense(client, gid)
        rv = client.get(f"/groups/{gid}")
        assert b"Dinner" in rv.data and b"30.00" in rv.data

    def test_split_validation_rejects_bad_percentage(self, client):
        # FR-02
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_expense(client, gid, split_type="percentage",
                    extra={"pct_1": "50"})
        rv = client.get(f"/groups/{gid}")
        assert b"Dinner" not in rv.data

    def test_split_validation_rejects_bad_exact(self, client):
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_expense(client, gid, split_type="exact", extra={"amt_1": "10.00"})
        rv = client.get(f"/groups/{gid}")
        assert b"Dinner" not in rv.data

    def test_split_accepts_valid_exact(self, client):
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_expense(client, gid, split_type="exact", extra={"amt_1": "30.00"})
        rv = client.get(f"/groups/{gid}")
        assert b"Dinner" in rv.data

    def test_edit_expense_recalculates(self, client):
        # FR-03
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_expense(client, gid, amount="30.00")
        client.post(f"/groups/{gid}/expenses/1/edit",
                    data={"title": "Dinner", "amount": "60.00", "payer_id": 1,
                          "split_type": "equal", "spent_on": "2025-01-15"})
        rv = client.get(f"/groups/{gid}")
        assert b"60.00" in rv.data and b"30.00" not in rv.data

    def test_delete_expense(self, client):
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_expense(client, gid)
        client.post(f"/groups/{gid}/expenses/1/delete")
        rv = client.get(f"/groups/{gid}")
        assert b"Dinner" not in rv.data

    def test_delete_warns_when_settlements_exist(self, client):
        # FR-04
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_member(client, gid, "b@x.com", "Bob")
        add_expense(client, gid, amount="30.00")  # bob owes alice 15
        record_settlement(client, gid, from_id=2, to_id=1, amount="10.00")
        rv = client.post(f"/groups/{gid}/expenses/1/delete",
                         follow_redirects=True)
        assert b"alter existing settlement" in rv.data
        # with confirm_warning it goes through
        rv = client.post(f"/groups/{gid}/expenses/1/delete",
                         data={"confirm_warning": "yes"},
                         follow_redirects=True)
        assert b"Expense deleted" in rv.data


class TestSettlements:
    def test_settlement_updates_balance(self, client):
        # FR-03, US-06
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_member(client, gid, "b@x.com", "Bob")
        add_expense(client, gid, amount="30.00")  # alice +15, bob -15
        record_settlement(client, gid, from_id=2, to_id=1, amount="15.00")
        rv = client.get(f"/groups/{gid}")
        assert b"Settlement recorded" in rv.data
        assert b"Everyone is settled up!" in rv.data

    def test_settlement_rejects_self_and_invalid(self, client):
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_member(client, gid, "b@x.com", "Bob")
        add_expense(client, gid, amount="30.00")
        rv = record_settlement(client, gid, from_id=1, to_id=1, amount="5.00")
        rv = client.get(f"/groups/{gid}")
        assert b"Settlement recorded" not in rv.data

    def test_settlement_plan_minimizes_transactions(self, client):
        # FR-05: 3 people, one payer -> exactly 2 transactions in the plan
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        add_member(client, gid, "b@x.com", "Bob")
        add_member(client, gid, "c@x.com", "Carol")
        add_expense(client, gid, amount="30.00")
        html = client.get(f"/groups/{gid}").get_data(as_text=True)
        plan_html = html.split("minimum transactions")[1]
        assert plan_html.count("<li><strong>") == 2  # bob->a and carol->a

    def test_cross_group_dashboard_summary(self, client):
        # US-11
        signup(client, ADMIN_EMAIL, "Alice")
        gid1 = make_group(client, name="Trip")
        gid2 = make_group(client, name="Flat")
        add_member(client, gid1, "b@x.com", "Bob")
        add_member(client, gid2, "b@x.com", "Bob")
        add_expense(client, gid1, amount="30.00")
        add_expense(client, gid2, amount="10.00")
        html = client.get("/dashboard").get_data(as_text=True)
        assert "Trip" in html and "Flat" in html
        assert "20.00" in html  # owed: 15 + 5 = 20.00

    def test_add_member_existing_account_joins_via_login(self, client):
        # A user that already exists joins by logging in, not signing up.
        signup(client, ADMIN_EMAIL, "Alice")
        gid = make_group(client)
        token = invite_email(client, gid, "bob@x.com")
        logout(client)
        signup(client, "bob@x.com", "Bob")
        rv = client.get(f"/invite/{token}")
        assert rv.status_code == 302
        assert b"Bob" in client.get(f"/groups/{gid}").data
