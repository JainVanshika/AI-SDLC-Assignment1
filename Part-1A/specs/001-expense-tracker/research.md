# Research: Expense and Budget Tracker

Decisions taken before design. Each one gives the decision, the reason and the alternatives considered.

## R1. Money as integer paise

- **Decision**: store and compute every amount as a whole number of paise; read user text with an ASCII-only pattern and integer arithmetic.
- **Reason**: constitution Principle I; `0.1 + 0.2` style rounding makes totals wrong by a paisa and exact assertions impossible. The pattern uses `[0-9]` because Python's `\d` also matches digits of other scripts (for example `٤٥٠`), and `int()` converts them to 450, so such text would be accepted although the specification refuses it.
- **Alternatives**: `decimal.Decimal` (exact, but allows many text forms such as exponents and `NaN` that the specification refuses, and needs context settings); floats (rejected by the constitution).

## R2. Dates are checked by pattern, then by calendar

- **Decision**: a date must match `YYYY-MM-DD` exactly and then be a real date through `datetime.date(y, m, d)`.
- **Reason**: `datetime.date.fromisoformat` in Python 3.12 also accepts `20261110` and week dates, which AC-006 must refuse. `datetime.date` rejects `2026-02-30` and `2027-02-29` and accepts `2028-02-29`.
- **Alternatives**: `strptime` (accepts `2026-1-5`, which AC-006 refuses); writing a leap-year function by hand (more code, more risk).

## R3. One JSON file, replaced atomically

- **Decision**: write the whole file to a temporary file in the same folder, flush and sync it, then `os.replace` it over the target.
- **Reason**: FR-019 and constitution Principle V; `os.replace` is atomic on the same file system, so a failure leaves either the old file or the new file, never half of one.
- **Alternatives**: appending to a log file (needs compaction and a repair step); SQLite (a binary file, outside the "one JSON file" decision of the specification).

## R4. A strict loader

- **Decision**: the loader validates the whole file and raises `storage-error` without changing it. A boolean or a float where an integer belongs is refused.
- **Reason**: FR-018 and AC-038, AC-039; `True` is an `int` in Python, so a plain `isinstance(x, int)` check would accept it.
- **Alternatives**: trusting the file; repairing it silently (both hide data loss).

## R5. Command line with `argparse`

- **Decision**: the standard library `argparse`, with shared options (`--file`, `--json`) added to every subcommand so they work after the subcommand name.
- **Reason**: no run-time dependency (plan constraint); exit codes are set by `main` from the `ExpenseError` code.
- **Alternatives**: `click` or `typer` (an extra dependency for no benefit here).

## R6. Independent check of totals

- **Decision**: the oracle builds an in-memory SQLite table (`id`, `amount_paise`, `category`, `date`) and computes totals with `SUM ... GROUP BY`, then compares with the library on 1,000 stores generated from a fixed seed.
- **Reason**: SC-002 asks for a check that is independent of the code under test; a SQL sum is a different method from the library's loop, and `sqlite3` is in the standard library.
- **Alternatives**: recomputing with the same loop in the test (not independent); `hypothesis` (an extra dependency; a seeded `random.Random` is enough).

## R7. Harness structure

- **Decision**: a small runner, `.harness/run_harness.py`, runs six gates as separate processes: lint (`ruff check --no-cache`), security (`bandit -r src -ll`), secrets (`gitleaks`), tests (`pytest --cov-branch --cov-fail-under=90`), traceability (every AC has a test that cites it), integrity (the frozen files still match the Git tag). It never imports the package.
- **Reason**: constitution Principles III and IV and the quality gates of the constitution. `-ll` makes Bandit report only medium and high findings, as the constitution states.
- **Alternatives**: a Makefile (less structured feedback); running the tools by hand (no single pass or fail result).
