# Quickstart: Expense and Budget Tracker

How to run the finished tool and check it. Commands are run from `Part-1A/`.

## Prerequisites

Python 3.12, [uv](https://docs.astral.sh/uv/), and gitleaks (`brew install gitleaks` on macOS).

## Install

```text
uv sync
```

## Try the reference data

```text
uv run expense add --amount 450.00 --category food --date 2026-11-10 --description lunch --file demo.json
uv run expense add --amount 120.50 --category food --date 2026-11-12 --file demo.json
uv run expense add --amount 300.00 --category travel --date 2026-11-15 --description bus --file demo.json
uv run expense add --amount 99.99 --category food --date 2026-10-31 --description snacks --file demo.json
uv run expense list --month 2026-11 --file demo.json
uv run expense totals --month 2026-11 --file demo.json
```

Expected: the list shows expenses 1, 2 and 3; the totals are food 570.50, travel 300.00, bills 0.00, other 0.00 and total 870.50 (AC-010, AC-014, AC-017).

## Budget warning

```text
uv run expense budget set --category food --amount 600.00 --file demo.json
uv run expense add --amount 20.00 --category food --date 2026-11-20 --file demo.json
uv run expense add --amount 50.00 --category food --date 2026-11-21 --file demo.json
```

Expected: the first add has no warning (total 590.50); the second is saved with `warning budget-exceeded: food 2026-11 total 640.50 limit 600.00` (AC-023). Both exit with status 0.

## Errors

```text
uv run expense add --amount 450.505 --category food --date 2026-11-10 --file demo.json; echo $?
```

Expected: `error invalid-amount: ...` on standard error and status 2 (AC-004).

```text
uv run expense delete 2 --file demo.json; echo $?
uv run expense delete 2 --yes --file demo.json
```

Expected: the first is refused with `confirmation-required` and status 2; the second deletes expense 2 (AC-046, AC-034).

## Run the checks

```text
uv run pytest tests -q
uv run python .harness/run_harness.py
```

The harness prints one line per gate and ends with `PASS` or `FAIL`. Results are written to `evidence/harness-results/<run-id>/`.

Delete `demo.json` when finished; it is only a trial file.
