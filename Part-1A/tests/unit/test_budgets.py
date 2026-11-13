import pytest
from expense_tracker.errors import ExpenseError
from helpers import reference_store

from expense_tracker import ops


def with_food_budget(limit: str):
    return ops.set_budget(reference_store(), "food", limit)


@pytest.mark.ac("AC-021")
def test_a_budget_is_stored_in_paise_and_replaced_by_a_new_one():
    store = ops.set_budget(reference_store(), "food", "600.00")
    assert store.budgets["food"] == 60000
    store = ops.set_budget(store, "food", "700.00")
    assert store.budgets["food"] == 70000
    assert len(store.budgets) == 1


@pytest.mark.ac("AC-022")
@pytest.mark.parametrize("amount", ["0", "-1", "abc"])
def test_a_bad_budget_amount_is_refused(amount):
    with pytest.raises(ExpenseError) as raised:
        ops.set_budget(reference_store(), "food", amount)
    assert raised.value.code == "invalid-amount"


@pytest.mark.ac("AC-022")
def test_a_budget_for_an_unknown_category_is_refused():
    with pytest.raises(ExpenseError) as raised:
        ops.set_budget(reference_store(), "x", "100.00")
    assert raised.value.code == "invalid-category"


@pytest.mark.ac("AC-023")
def test_the_expense_that_crosses_the_limit_is_saved_with_a_warning():
    store = with_food_budget("600.00")
    first = ops.add_expense(store, "20.00", "food", "2026-11-20")
    assert first.warnings == ()
    assert ops.monthly_totals(first.store, "2026-11")["food"] == 59050
    second = ops.add_expense(first.store, "50.00", "food", "2026-11-21")
    assert second.expense is not None
    assert second.expense in second.store.expenses
    assert len(second.warnings) == 1
    warning = second.warnings[0]
    assert (warning.category, warning.month, warning.total_paise, warning.limit_paise) == (
        "food",
        "2026-11",
        64050,
        60000,
    )


@pytest.mark.ac("AC-024")
def test_a_total_exactly_at_the_limit_does_not_warn_but_one_paisa_more_does():
    store = with_food_budget("600.00")
    at_limit = ops.add_expense(store, "29.50", "food", "2026-11-20")
    assert ops.monthly_totals(at_limit.store, "2026-11")["food"] == 60000
    assert at_limit.warnings == ()
    over = ops.add_expense(at_limit.store, "0.01", "food", "2026-11-20")
    assert len(over.warnings) == 1
    assert over.warnings[0].total_paise == 60001


@pytest.mark.ac("AC-025")
def test_a_category_without_a_budget_never_warns():
    store = with_food_budget("1.00")
    outcome = ops.add_expense(store, "9999999.00", "travel", "2026-11-20")
    assert outcome.warnings == ()


@pytest.mark.ac("AC-026")
def test_an_edit_that_crosses_the_limit_is_saved_with_a_warning():
    store = with_food_budget("600.00")
    at_limit = ops.edit_expense(store, 2, amount="150.00")
    assert at_limit.warnings == ()
    over = ops.edit_expense(store, 2, amount="150.01")
    assert [e.amount_paise for e in over.store.expenses if e.id == 2] == [15001]
    assert len(over.warnings) == 1
    assert over.warnings[0].total_paise == 60001


@pytest.mark.ac("AC-026")
def test_an_edit_is_checked_against_the_new_month_and_category():
    store = with_food_budget("600.00")
    outcome = ops.edit_expense(store, 4, date="2026-11-30")
    assert len(outcome.warnings) == 1
    warning = outcome.warnings[0]
    assert (warning.category, warning.month, warning.total_paise) == ("food", "2026-11", 67049)


@pytest.mark.ac("AC-027")
def test_only_the_total_of_the_month_of_the_expense_counts():
    store = with_food_budget("450.00")
    outcome = ops.add_expense(store, "1.00", "food", "2026-12-01")
    assert outcome.warnings == ()


@pytest.mark.ac("AC-028")
def test_budget_status_shows_limit_spent_and_remaining():
    store = with_food_budget("600.00")
    assert ops.budget_status(store, "2026-11") == [
        {"category": "food", "limit_paise": 60000, "spent_paise": 57050, "remaining_paise": 2950}
    ]
    store = ops.add_expense(store, "20.00", "food", "2026-11-20").store
    store = ops.add_expense(store, "50.00", "food", "2026-11-21").store
    status = ops.budget_status(store, "2026-11")
    assert status[0]["spent_paise"] == 64050
    assert status[0]["remaining_paise"] == -4050


@pytest.mark.ac("AC-028")
def test_budget_status_lists_only_categories_with_a_budget():
    assert ops.budget_status(reference_store(), "2026-11") == []


@pytest.mark.ac("AC-048")
def test_a_removed_budget_no_longer_warns_or_appears_in_the_status():
    store = ops.remove_budget(with_food_budget("600.00"), "food")
    assert ops.budget_status(store, "2026-11") == []
    assert ops.add_expense(store, "1000.00", "food", "2026-11-22").warnings == ()


@pytest.mark.ac("AC-049")
def test_removing_a_budget_that_was_never_set_is_not_found():
    with pytest.raises(ExpenseError) as raised:
        ops.remove_budget(reference_store(), "travel")
    assert raised.value.code == "not-found"


@pytest.mark.ac("AC-049")
def test_removing_the_budget_of_an_unknown_category_is_refused():
    with pytest.raises(ExpenseError) as raised:
        ops.remove_budget(reference_store(), "x")
    assert raised.value.code == "invalid-category"
