import pytest
from expense_tracker.errors import ExpenseError
from expense_tracker.models import Store

from expense_tracker import ops


@pytest.mark.ac("AC-001")
def test_the_first_expense_is_number_1_with_paise():
    outcome = ops.add_expense(Store.empty(), "450.00", "food", "2026-11-10", "lunch")
    expense = outcome.expense
    assert (
        expense.id,
        expense.amount_paise,
        expense.category,
        expense.date,
        expense.description,
    ) == (
        1,
        45000,
        "food",
        "2026-11-10",
        "lunch",
    )
    assert outcome.store.expenses == (expense,)
    assert outcome.store.next_id == 2
    assert outcome.warnings == ()


@pytest.mark.ac("AC-002")
def test_a_second_expense_without_description_is_number_2():
    first = ops.add_expense(Store.empty(), "450.00", "food", "2026-11-10", "lunch").store
    outcome = ops.add_expense(first, "120.50", "food", "2026-11-12")
    assert outcome.expense.id == 2
    assert outcome.expense.amount_paise == 12050
    assert outcome.expense.description == ""
    assert len(outcome.store.expenses) == 2


@pytest.mark.ac("AC-008")
@pytest.mark.parametrize(
    ("args", "code"),
    [
        (("0", "x", "2026-11-10", ""), "invalid-amount"),
        (("450", "x", "bad", ""), "invalid-category"),
        (("450", "food", "bad", "d" * 101), "invalid-date"),
        (("450", "food", "2026-11-10", "d" * 101), "invalid-description"),
        (("abc", "x", "bad", "d" * 101), "invalid-amount"),
    ],
)
def test_only_the_first_error_is_reported_in_the_fixed_order(args, code):
    with pytest.raises(ExpenseError) as raised:
        ops.add_expense(Store.empty(), *args)
    assert raised.value.code == code


@pytest.mark.ac("AC-009")
def test_a_refused_add_changes_nothing_and_uses_no_number():
    store = ops.add_expense(Store.empty(), "10.00", "food", "2026-11-10").store
    with pytest.raises(ExpenseError):
        ops.add_expense(store, "0", "food", "2026-11-10")
    assert len(store.expenses) == 1
    assert store.next_id == 2
    assert ops.add_expense(store, "5.00", "food", "2026-11-11").expense.id == 2


@pytest.mark.ac("AC-045")
@pytest.mark.parametrize("date", ["2099-12-31", "1900-01-01"])
def test_any_real_date_is_accepted_even_in_the_future(date):
    assert ops.add_expense(Store.empty(), "1.00", "other", date).expense.date == date


@pytest.mark.ac("AC-044")
@pytest.mark.parametrize(
    ("args", "code"),
    [
        (("1", "food", None), "invalid-date"),
        ((None, "food", "2026-11-10"), "invalid-amount"),
        (("1", None, "2026-11-10"), "invalid-category"),
    ],
)
def test_a_missing_value_is_refused_with_the_code_of_that_field(args, code):
    with pytest.raises(ExpenseError) as raised:
        ops.add_expense(Store.empty(), *args)
    assert raised.value.code == code
