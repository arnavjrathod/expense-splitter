"""Unit tests for the money math in app/algorithms.py."""
import pytest

from app.algorithms import (SplitValidationError, compute_balances,
                            simplify_debts, split_equal, validate_split)


class TestSplitEqual:
    def test_even_split(self):
        assert split_equal(1000, ["a", "b"]) == {"a": 500, "b": 500}

    def test_remainder_distributed_to_first_members(self):
        result = split_equal(1000, ["a", "b", "c"])
        assert sum(result.values()) == 1000
        assert result["a"] == 334 and result["b"] == 333

    def test_single_member(self):
        assert split_equal(777, ["a"]) == {"a": 777}


class TestValidateSplit:
    def test_equal_split_default_all_participants(self):
        result = validate_split(900, "equal", {}, ["a", "b", "c"])
        assert sum(result.values()) == 900

    def test_equal_split_subset(self):
        result = validate_split(900, "equal", {"a": 1, "b": 0}, ["a", "b", "c"])
        assert sum(result.values()) == 900
        assert set(result) == {"a"}

    def test_equal_split_no_participants_raises(self):
        with pytest.raises(SplitValidationError):
            validate_split(900, "equal", {"a": 0, "b": 0}, ["a", "b"])

    def test_percentage_ok(self):
        result = validate_split(10000, "percentage",
                                {"a": 6000, "b": 4000}, ["a", "b"])
        assert result == {"a": 6000, "b": 4000}

    def test_percentage_must_total_100(self):
        with pytest.raises(SplitValidationError):
            validate_split(10000, "percentage", {"a": 6000, "b": 3000}, ["a", "b"])

    def test_exact_ok(self):
        result = validate_split(5000, "exact", {"a": 3000, "b": 2000}, ["a", "b"])
        assert result == {"a": 3000, "b": 2000}

    def test_exact_must_total_amount(self):
        with pytest.raises(SplitValidationError):
            validate_split(5000, "exact", {"a": 3000, "b": 1000}, ["a", "b"])

    def test_non_participant_raises(self):
        with pytest.raises(SplitValidationError):
            validate_split(5000, "exact", {"a": 3000, "z": 2000}, ["a", "b"])

    def test_zero_amount_raises(self):
        with pytest.raises(SplitValidationError):
            validate_split(0, "equal", {}, ["a"])

    def test_unknown_type_raises(self):
        with pytest.raises(SplitValidationError):
            validate_split(100, "weird", {}, ["a"])


class TestComputeBalances:
    def test_simple_expense(self):
        expenses = [{"payer_id": "a", "amount_cents": 3000,
                     "shares": {"a": 1000, "b": 1000, "c": 1000}}]
        balances = compute_balances(expenses, [])
        assert balances == {"a": 2000, "b": -1000, "c": -1000}

    def test_settlement_zeroes_out(self):
        expenses = [{"payer_id": "a", "amount_cents": 3000,
                     "shares": {"a": 1000, "b": 1000, "c": 1000}}]
        settlements = [{"from_id": "b", "to_id": "a", "amount_cents": 1000}]
        balances = compute_balances(expenses, settlements)
        assert balances["a"] == 1000
        assert balances["b"] == 0
        assert balances["c"] == -1000

    def test_empty_group(self):
        assert compute_balances([], []) == {}

    def test_round_trip_sum_is_zero(self):
        expenses = [
            {"payer_id": "a", "amount_cents": 5000,
             "shares": {"a": 2000, "b": 1500, "c": 1500}},
            {"payer_id": "b", "amount_cents": 2500,
             "shares": {"b": 1000, "a": 500, "c": 1000}},
        ]
        settlements = [{"from_id": "c", "to_id": "a", "amount_cents": 800}]
        balances = compute_balances(expenses, settlements)
        assert sum(balances.values()) == 0


class TestSimplifyDebts:
    def test_no_debts(self):
        assert simplify_debts({}) == []

    def test_single_pair(self):
        plan = simplify_debts({"a": 1000, "b": -1000})
        assert plan == [{"from_id": "b", "to_id": "a", "amount_cents": 1000}]

    def test_minimal_transaction_count(self):
        # a paid 30, b paid 0, c paid 0 -> raw pairwise debts would be 2
        # transactions; simplification must also produce exactly 2 (b->a, c->a)
        balances = {"a": 3000, "b": -1500, "c": -1500}
        plan = simplify_debts(balances)
        assert len(plan) == 2
        assert sum(t["amount_cents"] for t in plan if t["to_id"] == "a") == 3000

    def test_chain_simplifies(self):
        # b owes a and c owes b; simplified: c -> a directly, 1 transaction
        balances = {"a": 1000, "b": 0, "c": -1000}
        plan = simplify_debts(balances)
        assert len(plan) == 1
        assert plan[0]["from_id"] == "c" and plan[0]["to_id"] == "a"

    def test_plan_zeroes_all_balances(self):
        balances = {"a": 700, "b": -300, "c": -500, "d": 100}
        plan = simplify_debts(balances)
        net = dict(balances)
        for t in plan:
            net[t["from_id"]] += t["amount_cents"]
            net[t["to_id"]] -= t["amount_cents"]
        assert all(v == 0 for v in net.values())

    def test_min_transaction_count_property(self):
        # 1 creditor + 2 debtors can always be settled in 2 transactions
        balances = {"a": 900, "b": -400, "c": -500}
        assert len(simplify_debts(balances)) == 2
