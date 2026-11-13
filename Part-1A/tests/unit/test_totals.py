import pytest
from expense_tracker.errors import ExpenseError
from helpers import reference_store

from expense_tracker import ops


@pytest.mark.ac("AC-017")
def test_november_totals():
    assert ops.monthly_totals(reference_store(), "2026-11") == {
        "food": 57050,
        "travel": 30000,
        "bills": 0,
        "other": 0,
        "overall": 87050,
    }


@pytest.mark.ac("AC-018")
def test_october_totals_do_not_include_november():
    assert ops.monthly_totals(reference_store(), "2026-10") == {
        "food": 9999,
        "travel": 0,
        "bills": 0,
        "other": 0,
        "overall": 9999,
    }


@pytest.mark.ac("AC-019")
def test_a_month_with_no_expenses_is_all_zero():
    assert ops.monthly_totals(reference_store(), "2026-12") == {
        "food": 0,
        "travel": 0,
        "bills": 0,
        "other": 0,
        "overall": 0,
    }


@pytest.mark.ac("AC-020")
def test_a_bad_month_is_refused():
    with pytest.raises(ExpenseError) as raised:
        ops.monthly_totals(reference_store(), "2026-13")
    assert raised.value.code == "invalid-month"
