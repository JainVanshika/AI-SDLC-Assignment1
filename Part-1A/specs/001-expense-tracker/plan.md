# Implementation Plan: Expense and Budget Tracker

**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-expense-tracker/spec.md`

## Summary

A library of small pure functions that keeps expenses and monthly category budgets, plus a thin command line, all stored in one JSON file. Money is a whole number of paise end to end. The core never reads the clock, the disk or the network; one storage module reads the file and writes it atomically. Every operation of the specification (add, list with filters, edit, delete, monthly totals, set, remove and report budgets) is a function on an immutable `Store` value that returns a new `Store` plus the result and any warnings.

## Technical Context

**Language/Version**: Python 3.12 (`requires-python >=3.12,<3.13`), managed with uv

**Primary Dependencies**: none at run time (standard library only: `json`, `re`, `datetime`, `os`, `tempfile`, `argparse`, `sys`, `dataclasses`)

**Development tools**: pytest, pytest-cov, Ruff, Bandit; gitleaks as an external program

**Storage**: one JSON file, replaced atomically on every write

**Testing**: pytest with branch coverage; the oracle for totals is an independent SQLite (standard library) integer computation

**Target Platform**: any computer with Python 3.12 and a terminal

**Project Type**: library and command line

**Performance Goals**: list and totals for 10,000 expenses in under 2 seconds (SC-003)

**Constraints**: no floating-point money, no clock, no random numbers, no network (FR-022); no run-time dependencies unless justified here

**Scale/Scope**: one user, up to tens of thousands of expenses, four categories

## Constitution Check

*Gate: passes before research and again after design.*

| Principle | How the design satisfies it |
|---|---|
| I. Exact Money | `money.py` parses the text with an ASCII-only pattern and integer arithmetic; no `float` appears in any module; the file stores `amount_paise` as an integer and the loader rejects any other type |
| II. Library First | `ops.py` has pure functions on a `Store`; `storage.py` is the only module that touches the disk; `cli.py` only parses arguments, calls the library and prints; every date is an argument |
| III. Specified Before Built | The requirement map below ties every FR to a module; tasks will cite FR and AC IDs; tests carry an `ac` marker with the AC ID |
| IV. Independent Harness | `.harness/` is a separate program that runs tools and never imports `expense_tracker`; tests, harness and thresholds are frozen under a Git tag before implementation |
| V. Safe by Default | All input is checked before use, errors carry code and field, the file is written to a temporary file in the same folder and swapped in with `os.replace`, and the loader refuses a malformed file without changing it |

No violations. No complexity needs justifying.

## Key Decisions

- **D1. Immutable store, pure operations.** `Store` is a frozen dataclass holding a tuple of expenses, a mapping of budgets and `next_id`. Each operation returns a new `Store`. This makes every acceptance criterion testable without a file (FR-001 to FR-016, FR-022, FR-023).
- **D2. Amount parsing.** The pattern `^(0|[1-9][0-9]*)(\.[0-9]{1,2})?$` is applied with `re.fullmatch`. `[0-9]` is used and not `\d`, because `\d` also matches digits of other scripts. The paise value is `int(whole) * 100 + int(fraction.ljust(2, "0"))`. The result must be between 1 and 1,000,000,000 (FR-002, FR-003).
- **D3. Dates and months.** A date must match `^[0-9]{4}-[0-9]{2}-[0-9]{2}$` and then be accepted by `datetime.date(year, month, day)`, so `2027-02-29` is refused. A month must match `^[0-9]{4}-(0[1-9]|1[0-2])$`. `date.fromisoformat` is not used because it accepts other forms (FR-005, FR-010).
- **D4. Error order.** Validation runs in the order amount, category, date, description and raises `ExpenseError(code, message, field)` for the first failure; nothing is changed (FR-007).
- **D5. Warnings are results.** `add_expense` and `edit_expense` return `warnings`, a list of `budget-exceeded` records with category, month, total and limit. A total equal to the limit does not warn (FR-013).
- **D6. Atomic save.** `save` writes a temporary file in the target folder, flushes and syncs it, then calls `os.replace`. On any failure the temporary file is removed and the old file stays (FR-019).
- **D7. Strict load.** `load` checks version, `next_id`, unique ids, integer types (a `bool` or a float is refused), categories, dates and description length. Anything wrong raises `storage-error` and the file is not written (FR-018).
- **D8. Command line.** Subcommands `add`, `list`, `edit`, `delete`, `totals`, `budget set`, `budget remove`, `budget status`. `--file` (default `expenses.json`) and `--json` are accepted after the subcommand. `delete` needs `--yes`. Exit codes 0, 2 and 3 (FR-016, FR-017, FR-020, FR-021).
- **D9. Oracle.** The tests compute monthly totals and budget overruns for 1,000 seeded random stores using an in-memory SQLite table with integer columns, a different method from the library's loops (SC-002).

## Requirement Map

| Requirement | Module |
|---|---|
| FR-001, FR-007, FR-015, FR-016 | `ops.py` (`add_expense`, `edit_expense`, `delete_expense`), `errors.py` |
| FR-002, FR-003 | `money.py` |
| FR-004, FR-005, FR-006, FR-010 | `rules.py` |
| FR-008, FR-009 | `ops.py` (`list_expenses`) |
| FR-011 | `ops.py` (`monthly_totals`) |
| FR-012, FR-013, FR-014, FR-023 | `ops.py` (`set_budget`, `remove_budget`, `budget_status`, warning check) |
| FR-017, FR-018, FR-019 | `storage.py` |
| FR-020, FR-021 | `cli.py`, `render.py` |
| FR-022 | no module reads the clock or network; checked by a test that imports the modules and scans for forbidden names |

## Project Structure

### Documentation (this feature)

```text
specs/001-expense-tracker/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   ├── library.md
│   └── store.schema.json
├── checklists/requirements.md
└── tasks.md          (created by the tasks step)
```

### Source Code (repository root: `Part-1A/`)

```text
src/expense_tracker/
├── __init__.py
├── errors.py     # ExpenseError(code, message, field)
├── money.py      # parse_amount, format_rupees
├── rules.py      # check_category, check_date, check_month, check_description, check_id
├── models.py     # Expense, Store, Warning (frozen dataclasses)
├── ops.py        # the operations, pure functions
├── storage.py    # load, save (atomic)
├── render.py     # text and JSON output
└── cli.py        # main(argv) -> int

tests/
├── conftest.py   # the "ac" marker
├── unit/         # money, rules, ops, storage, render
├── integration/  # the command line in a subprocess, with a temporary folder
├── property/     # seeded random checks of invariants
└── oracle/       # SQLite integer check of totals and warnings

.harness/         # separate program: lint, security, secrets, tests, traceability, integrity
evidence/         # initial-generation/, final-generation/, harness-results/, harness-log.md
pyproject.toml
```

**Structure Decision**: a single Python package with a thin command line, as the constitution requires (Principle II). The harness lives outside the package and runs the tools as subprocesses.
