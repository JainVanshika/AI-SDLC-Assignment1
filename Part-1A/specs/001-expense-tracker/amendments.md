# Amendments

Changes to anything frozen under the baseline tag (the tests, the harness, the specification or `pyproject.toml`). Each one is recorded here and gets a new baseline tag; earlier tags are never moved.

## A1. Import order in the tests, and the integrity gate follows the newest tag

- **Tag**: `baseline-1a-before-implement-v2`.
- **Trigger**: run 1 of the harness (`evidence/harness-results/run-1/`) failed the lint gate with 12 findings, all `I001` (import block not sorted), all in `tests/`. The other five gates passed, including all 1,193 tests with 96.53% branch coverage.
- **Cause**: when the test imports were tidied before the baseline, only `src/expense_tracker/__init__.py` existed, so Ruff sorted `expense_tracker.errors` and `expense_tracker.models` as third-party. Once the implementation modules existed, Ruff treated `expense_tracker` as first-party and wanted those imports in their own block.
- **Change**:
  - The import blocks of 12 test files were re-sorted with `ruff check tests --select I001 --fix`. A script compared each file with the baseline version after removing import lines and blank lines, and found no other difference in any of the 12 files. No test, assertion, threshold or criterion changed.
  - `.harness/gates/integrity.py` now compares with the newest tag that matches `baseline-1a-before-implement*`, so that an amendment can advance the baseline without moving an old tag. Nothing else in the harness changed.
- **Not changed**: `src/` (the first generation is untouched), `spec.md`, `pyproject.toml`, the thresholds, the Ruff rules.
- **Re-execution**: the same six gates, run again as run 2.
