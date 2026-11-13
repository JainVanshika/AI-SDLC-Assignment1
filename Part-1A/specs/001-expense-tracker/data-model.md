# Data Model: Expense and Budget Tracker

## Entities

### Expense

| Field | Type | Rule | Requirement |
|---|---|---|---|
| `id` | integer | 1 or more; unique; never reused | FR-001 |
| `amount_paise` | integer | 1 to 1,000,000,000 | FR-002, FR-003 |
| `category` | text | exactly `food`, `travel`, `bills` or `other` | FR-004 |
| `date` | text | a real calendar date, `YYYY-MM-DD` | FR-005 |
| `description` | text | 0 to 100 characters | FR-006 |

### Budget

A category (one of the four) and its monthly limit in paise, 1 to 1,000,000,000. At most one per category.

### Store

| Field | Type | Rule |
|---|---|---|
| `expenses` | list of Expense | any order on disk; always listed by date, then id |
| `budgets` | map category to limit | only categories that have a budget |
| `next_id` | integer | greater than every id ever issued; starts at 1 |

### Warning

`budget-exceeded` with `category`, `month`, `total_paise` and `limit_paise`. It is a result, never stored.

## Derived values

- **Month of an expense**: the first seven characters of its date (`YYYY-MM`).
- **Total**: for a category and a month, the sum of `amount_paise` of the matching expenses.
- **Spent and remaining** (budget status): `spent` is the total; `remaining = limit - spent`, which can be negative.
- **Warning rule**: after an add or an edit, if the category has a budget and its total in the month of the saved expense is greater than the limit, a warning is returned (FR-013). Only the month and category of the saved expense are checked.

## State changes

| Operation | Effect on the store |
|---|---|
| add | appends the expense with `id = next_id`; `next_id` goes up by 1 |
| edit | replaces the given fields of one expense; `id` and `next_id` unchanged |
| delete | removes one expense; `next_id` unchanged, so the number is never reused |
| budget set | sets or replaces one limit |
| budget remove | removes one limit |
| list, totals, budget status | none |

A refused operation changes nothing, and does not use up an id (AC-009).

## File format

One JSON object (the schema is in [contracts/store.schema.json](contracts/store.schema.json)):

```json
{
  "version": 1,
  "next_id": 5,
  "expenses": [
    {"id": 1, "amount_paise": 45000, "category": "food", "date": "2026-11-10", "description": "lunch"}
  ],
  "budgets": {"food": 60000}
}
```

The loader refuses (with `storage-error`) a file that is not valid JSON, has another `version`, has a missing field or an extra field, has a boolean or a float where an integer belongs, has a category or date that breaks the rules above, has a repeated `id`, or has a `next_id` that is not greater than every `id`.
