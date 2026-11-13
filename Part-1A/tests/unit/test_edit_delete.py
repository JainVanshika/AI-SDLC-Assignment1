import pytest
from expense_tracker.errors import ExpenseError
from helpers import ids, reference_store

from expense_tracker import ops


def find(store, expense_id):
    return next(e for e in store.expenses if e.id == expense_id)


@pytest.mark.ac("AC-029")
def test_editing_the_amount_changes_only_the_amount():
    store = reference_store()
    before = find(store, 1)
    after = find(ops.edit_expense(store, 1, amount="500.00").store, 1)
    assert after.amount_paise == 50000
    assert (after.id, after.category, after.date, after.description) == (
        before.id,
        before.category,
        before.date,
        before.description,
    )


@pytest.mark.ac("AC-030")
def test_category_date_and_description_can_each_be_changed_alone():
    store = reference_store()
    assert find(ops.edit_expense(store, 1, category="bills").store, 1).category == "bills"
    assert find(ops.edit_expense(store, 1, date="2026-11-11").store, 1).date == "2026-11-11"
    assert find(ops.edit_expense(store, 1, description="dinner").store, 1).description == "dinner"
    assert find(ops.edit_expense(store, 1, description="").store, 1).description == ""


@pytest.mark.ac("AC-030")
@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("category", "x", "invalid-category"),
        ("date", "2026-02-30", "invalid-date"),
        ("description", "d" * 101, "invalid-description"),
    ],
)
def test_an_edit_follows_the_same_rules_as_an_add(field, value, code):
    with pytest.raises(ExpenseError) as raised:
        ops.edit_expense(reference_store(), 1, **{field: value})
    assert raised.value.code == code


@pytest.mark.ac("AC-031")
def test_an_edit_with_nothing_to_change_is_refused():
    with pytest.raises(ExpenseError) as raised:
        ops.edit_expense(reference_store(), 1)
    assert raised.value.code == "nothing-to-change"


@pytest.mark.ac("AC-032")
def test_an_edit_with_an_invalid_value_is_refused_and_changes_nothing():
    store = reference_store()
    with pytest.raises(ExpenseError) as raised:
        ops.edit_expense(store, 1, amount="0")
    assert raised.value.code == "invalid-amount"
    assert find(store, 1).amount_paise == 45000


@pytest.mark.ac("AC-033")
def test_a_valid_id_that_does_not_exist_is_not_found():
    with pytest.raises(ExpenseError) as raised:
        ops.edit_expense(reference_store(), 99, amount="1.00")
    assert raised.value.code == "not-found"
    with pytest.raises(ExpenseError) as raised:
        ops.delete_expense(reference_store(), 99)
    assert raised.value.code == "not-found"


@pytest.mark.ac("AC-033")
@pytest.mark.parametrize("bad", ["abc", "0", "-1", "1.5"])
def test_a_bad_id_is_invalid(bad):
    with pytest.raises(ExpenseError) as raised:
        ops.delete_expense(reference_store(), bad)
    assert raised.value.code == "invalid-id"


@pytest.mark.ac("AC-034")
def test_a_deleted_expense_leaves_the_list_and_the_totals():
    store = ops.delete_expense(reference_store(), 2)
    assert ids(ops.list_expenses(store)) == [4, 1, 3]
    assert ops.monthly_totals(store, "2026-11")["overall"] == 75000


@pytest.mark.ac("AC-035")
def test_numbers_are_never_reused():
    store = ops.delete_expense(reference_store(), 4)
    assert ops.add_expense(store, "1.00", "other", "2026-11-20").expense.id == 5
