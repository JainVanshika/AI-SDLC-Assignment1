import pytest
from helpers import ids, reference_store

from expense_tracker import ops
from expense_tracker.errors import ExpenseError
from expense_tracker.models import Store


@pytest.mark.ac("AC-010")
def test_everything_is_listed_by_date_oldest_first():
    assert ids(ops.list_expenses(reference_store())) == [4, 1, 2, 3]


@pytest.mark.ac("AC-011")
def test_expenses_on_the_same_date_are_listed_by_number():
    store = Store.empty()
    store = ops.add_expense(store, "10.00", "other", "2026-12-01").store
    store = ops.add_expense(store, "5.00", "other", "2026-12-01").store
    assert ids(ops.list_expenses(store, month="2026-12")) == [1, 2]


@pytest.mark.ac("AC-012")
def test_an_empty_store_and_a_filter_with_no_match_give_an_empty_list():
    assert ops.list_expenses(Store.empty()) == ()
    assert ops.list_expenses(reference_store(), category="bills") == ()
    assert ops.list_expenses(reference_store(), month="2026-12") == ()


@pytest.mark.ac("AC-013")
def test_filter_by_category():
    assert ids(ops.list_expenses(reference_store(), category="food")) == [4, 1, 2]


@pytest.mark.ac("AC-014")
def test_filter_by_month():
    assert ids(ops.list_expenses(reference_store(), month="2026-11")) == [1, 2, 3]


@pytest.mark.ac("AC-015")
def test_filter_by_category_and_month_means_both_must_match():
    assert ids(ops.list_expenses(reference_store(), category="food", month="2026-11")) == [1, 2]


@pytest.mark.ac("AC-016")
def test_a_bad_filter_is_refused():
    with pytest.raises(ExpenseError) as raised:
        ops.list_expenses(reference_store(), category="x")
    assert raised.value.code == "invalid-category"
    for month in ["2026-13", "2026-1", "Nov"]:
        with pytest.raises(ExpenseError) as raised:
            ops.list_expenses(reference_store(), month=month)
        assert raised.value.code == "invalid-month"
