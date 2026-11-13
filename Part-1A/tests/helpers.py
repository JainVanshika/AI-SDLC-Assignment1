"""Builders for the reference data of the specification."""

from expense_tracker.models import Store

from expense_tracker import ops


def reference_store() -> Store:
    """The four reference expenses (ids 1 to 4) of the specification."""
    store = Store.empty()
    store = ops.add_expense(store, "450.00", "food", "2026-11-10", "lunch").store
    store = ops.add_expense(store, "120.50", "food", "2026-11-12").store
    store = ops.add_expense(store, "300.00", "travel", "2026-11-15", "bus").store
    store = ops.add_expense(store, "99.99", "food", "2026-10-31", "snacks").store
    return store


def ids(expenses) -> list[int]:
    return [e.id for e in expenses]
