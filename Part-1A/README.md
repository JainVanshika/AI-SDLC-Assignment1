# Expense and Budget Tracker (Part 1A)

A personal expense tracker. It records expenses with an amount in rupees, a category, a date and an optional note; lists and filters them; shows monthly totals per category; keeps a monthly budget limit per category and warns when an expense takes a category over its limit. It is a Python library and a command line, and everything is kept in one JSON file.

Money is always a whole number of paise, never a floating-point number. The tool never reads the clock, so every date is given by the person.

## Install

Python 3.12 and [uv](https://docs.astral.sh/uv/) are needed. From this folder:

```text
uv sync
```

The harness also uses gitleaks to scan for secrets: `brew install gitleaks` on macOS, or see the gitleaks documentation for other platforms.

## Use

```text
$ uv run expense add --amount 450.00 --category food --date 2026-11-10 --description lunch
added #1  450.00  food    2026-11-10  lunch

$ uv run expense add --amount 300.00 --category travel --date 2026-11-15 --description bus
added #2  300.00  travel  2026-11-15  bus

$ uv run expense list --month 2026-11
#1  450.00  food    2026-11-10  lunch
#2  300.00  travel  2026-11-15  bus

$ uv run expense totals --month 2026-11
food 450.00
travel 300.00
bills 0.00
other 0.00
total 750.00

$ uv run expense budget set --category food --amount 400.00
budget food 400.00

$ uv run expense add --amount 20.00 --category food --date 2026-11-20
added #3  20.00  food    2026-11-20
warning budget-exceeded: food 2026-11 total 470.00 limit 400.00
```

| Command | Options |
|---|---|
| `expense add` | `--amount A --category C --date D [--description T]` |
| `expense list` | `[--category C] [--month YYYY-MM]` |
| `expense edit ID` | `[--amount A] [--category C] [--date D] [--description T]` |
| `expense delete ID` | `--yes` |
| `expense totals` | `--month YYYY-MM` |
| `expense budget set` | `--category C --amount A` |
| `expense budget remove` | `--category C` |
| `expense budget status` | `--month YYYY-MM` |

Every command also accepts `--file PATH` (the default is `expenses.json` in the current folder) and `--json` (print JSON, with amounts as integers in paise).

- Amounts are written in rupees with up to two decimals (`450`, `450.5`, `450.50`), more than 0 and at most `10000000.00`.
- Categories are `food`, `travel`, `bills` and `other`. Dates are `YYYY-MM-DD`; months are `YYYY-MM`.
- A budget is a monthly limit for one category. An expense that takes the month's total above the limit is still saved, and a `budget-exceeded` warning is shown. A total exactly at the limit does not warn.
- Deleting needs `--yes` on the command line.

Success exits with 0 (also when there is a warning), invalid input or a missing expense with 2, and a damaged data file with 3. Errors go to standard error as `error <code>: <message>`, and nothing is written to standard output.

The library is used as `expense_tracker.ops` (the operations), `expense_tracker.storage` (load and save) and `expense_tracker.money`. See [`specs/001-expense-tracker/contracts/library.md`](specs/001-expense-tracker/contracts/library.md).

## Harness

```text
uv run pytest tests -q                      # the tests
uv run python .harness/run_harness.py       # the six gates
```

The runner executes six gates as separate processes: lint (Ruff, no cache), security (Bandit, medium and high findings), secrets (gitleaks, history and files), tests (pytest, branch coverage of at least 90%), traceability (every acceptance criterion is cited by a test) and integrity (the tests, the harness, the specification and `pyproject.toml` match the newest baseline tag). It ends with `PASS` or `FAIL` and writes its results to `evidence/harness-results/<run-id>/`, with a `feedback.json` when a gate fails.

## Layout

```text
src/expense_tracker/   the library and the command line
tests/                 unit, integration, property and oracle tests
.harness/              the gates and the runner (never imports the library)
specs/001-expense-tracker/   specification, plan, tasks, contracts, amendments
evidence/              initial and final generation, harness results, harness log
```

## Limits

- One user and one local file; two programs writing the file at the same moment can lose one update.
- Only the Indian rupee, a fixed list of four categories, and one budget limit per category for every month.
- Checked on macOS only.
