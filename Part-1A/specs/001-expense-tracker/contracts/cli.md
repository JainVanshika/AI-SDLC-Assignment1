# Contract: command line

The program is called `expense`. Every subcommand accepts `--file PATH` (default `expenses.json` in the current folder) and `--json` (print JSON instead of text).

| Command | Options | Spec |
|---|---|---|
| `expense add` | `--amount A --category C --date D [--description T]` | FR-001 to FR-007 |
| `expense list` | `[--category C] [--month YYYY-MM]` | FR-008 to FR-010 |
| `expense edit ID` | `[--amount A] [--category C] [--date D] [--description T]` | FR-015 |
| `expense delete ID` | `--yes` | FR-016 |
| `expense totals` | `--month YYYY-MM` | FR-011 |
| `expense budget set` | `--category C --amount A` | FR-012 |
| `expense budget remove` | `--category C` | FR-023 |
| `expense budget status` | `--month YYYY-MM` | FR-014 |

`--description ""` on `edit` sets an empty description. An `edit` with none of the four value options is `nothing-to-change`. Option values are read as text and checked by the library, so every error code comes from the same rules whether the call is made from the command line or the library.

## Exit status and errors

| Status | Meaning |
|---|---|
| 0 | success, with or without warnings |
| 2 | invalid input, `not-found` or `confirmation-required` |
| 3 | `storage-error` |

An error is written to standard error as `error <code>: <message>`; nothing is written to standard output (FR-021). Error codes: `invalid-amount`, `invalid-category`, `invalid-date`, `invalid-description`, `invalid-month`, `invalid-id`, `not-found`, `nothing-to-change`, `confirmation-required`, `storage-error`.

## Text output

Amounts are shown in rupees with two decimals (`120.50`), computed from the integer by integer arithmetic.

```text
$ expense add --amount 450.00 --category food --date 2026-11-10 --description lunch
added #1  450.00  food  2026-11-10  lunch

$ expense list --month 2026-11
#1  450.00  food    2026-11-10  lunch
#2  120.50  food    2026-11-12
#3  300.00  travel  2026-11-15  bus

$ expense totals --month 2026-11
food 570.50
travel 300.00
bills 0.00
other 0.00
total 870.50
```

A warning is printed after the result as `warning budget-exceeded: food 2026-11 total 640.50 limit 600.00`.

## JSON output (`--json`)

Amounts are integers in paise. Output is one object on one line, with keys in sorted order.

| Command | Shape |
|---|---|
| `add`, `edit` | `{"expense": {id, amount_paise, category, date, description}, "warnings": [{category, month, total_paise, limit_paise}]}` |
| `list` | `{"expenses": [ ... ]}` |
| `delete` | `{"deleted": ID}` |
| `totals` | `{"month": "2026-11", "totals": {"food": 57050, "travel": 30000, "bills": 0, "other": 0}, "overall": 87050}` |
| `budget set` | `{"budget": {"category": "food", "limit_paise": 60000}}` |
| `budget remove` | `{"removed": "food"}` |
| `budget status` | `{"month": "2026-11", "budgets": [{"category": "food", "limit_paise": 60000, "spent_paise": 57050, "remaining_paise": 2950}]}` |

The JSON equals what the library returns for the same call (AC-042).
