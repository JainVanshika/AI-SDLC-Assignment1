# Contract: library

Package `expense_tracker`. Amounts come in as text in rupees (`"450.50"`) and go out as integer paise. Dates are text `YYYY-MM-DD`, months `YYYY-MM`. Every function that fails raises `ExpenseError` with `code`, `message` and `field`, and changes nothing.

## Types

- `Store`: frozen; `expenses` (tuple of `Expense`), `budgets` (read-only mapping category to paise), `next_id` (int). `Store.empty()` returns `Store((), {}, 1)`.
- `Expense`: frozen; `id`, `amount_paise`, `category`, `date`, `description`.
- `Warning`: frozen; `category`, `month`, `total_paise`, `limit_paise`.
- `Outcome`: frozen; `store` (the new `Store`), `expense` (or `None`), `warnings` (tuple of `Warning`).

## Operations (module `expense_tracker.ops`)

| Function | Returns | Spec |
|---|---|---|
| `add_expense(store, amount, category, date, description="")` | `Outcome` | FR-001 to FR-007, FR-013 |
| `edit_expense(store, expense_id, amount=None, category=None, date=None, description=None)` | `Outcome` | FR-015, FR-013 |
| `delete_expense(store, expense_id)` | new `Store` | FR-016 |
| `list_expenses(store, category=None, month=None)` | tuple of `Expense`, ordered by date then id | FR-008 to FR-010 |
| `monthly_totals(store, month)` | `dict` of the four categories to paise, plus `"overall"` | FR-011 |
| `set_budget(store, category, amount)` | new `Store` | FR-012 |
| `remove_budget(store, category)` | new `Store` | FR-023 |
| `budget_status(store, month)` | list of `{category, limit_paise, spent_paise, remaining_paise}` | FR-014 |

`expense_id` is accepted as text or an integer and checked by the rules of FR-016 (`invalid-id`, then `not-found`). `None` for an optional value in `edit_expense` means "leave unchanged"; an empty string for `description` means "clear it".

## Storage (module `expense_tracker.storage`)

| Function | Behaviour | Spec |
|---|---|---|
| `load(path)` | returns a `Store`; a missing file gives `Store.empty()`; a bad file raises `storage-error` and is not changed | FR-017, FR-018 |
| `save(path, store)` | writes atomically; on failure the old file is unchanged and `storage-error` is raised | FR-017, FR-019 |

## Money (module `expense_tracker.money`)

| Function | Behaviour | Spec |
|---|---|---|
| `parse_amount(text)` | text in rupees to integer paise, or `invalid-amount` | FR-002, FR-003 |
| `format_rupees(paise)` | integer paise to `"120.50"` using integer arithmetic | FR-020 |
