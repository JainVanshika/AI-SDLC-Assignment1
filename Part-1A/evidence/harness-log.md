# Harness log: Part 1A

## 1. First generation and its context

The Spec Kit stages were completed and committed in order: setup, constitution, specify, clarify, plan, tasks and analyze. The specification has 23 requirements, 49 acceptance criteria, 7 user stories and 5 clarifications, and the task list has 37 tasks. The harness and the tests were written and frozen before any implementation.

The agent then implemented the approved artifacts, and the first generation was copied unchanged before the first harness run, so that it stayed fixed.

The coding agent was Claude Code (Sonnet 5.5). I chose the problem, approved the constitution, answered the clarification questions, and read the specification, plan and tasks before the implementation began.

Stage commits: `CONST-1` `75d6854`, `SPEC-1` `624b8fe`, `CLAR-1` `97d290a`, `PLAN-1` `166a794`, `TASKS-1` `d2ff781`, `ANALYZE-1` `1725767`.

The baseline tag `baseline-1a-before-implement` (annotation `test_functions=81`) is on commit `0bddaea`. It froze the harness, `tests/`, `spec.md` and `pyproject.toml`.

The first generation is commit `cba089f`, copied unchanged to `evidence/initial-generation/expense_tracker/` (8 modules plus `__main__.py`, 631 lines in all).

The analysis step found three small issues before the implementation:

- a Ruff rule set that would have flagged `assert` in the tests;
- an incorrect module name in a test helper;
- a clock test that missed calls such as `date.today()` and `datetime.now()`.

They were fixed in the tasks (`specs/001-expense-tracker/analysis.md`).

The tests were written before the code, from the acceptance criteria, and the first generation passed five of the six gates in its first run.

## 2. Harness setup

The harness has six gates. Each tool runs as a separate process, and the harness never imports the application. The rules were fixed in advance and come from the constitution.

| Gate | What it checks | Tool |
|---|---|---|
| lint | no findings, cache switched off | Ruff 0.17.5 |
| security | no medium or high finding | Bandit 1.9.4 (`-ll`) |
| secrets | Git history and project files, no allowlist | gitleaks 8.30.1 |
| tests | all tests pass, branch coverage at least 90% | pytest 9.2.0, pytest-cov |
| traceability | every acceptance criterion is cited by a test, and no test cites an unknown one | the harness itself |
| integrity | tests, harness, `spec.md` and `pyproject.toml` match the newest baseline tag | Git |

The environment was Python 3.12.15, uv 0.12.24 and macOS.

There are 81 test functions, which become 1,193 test cases. One independent check runs 1,000 random stores and compares the library's totals and budget warnings with integer sums calculated in SQLite; the other 193 cases are ordinary tests.

Four Ruff rules are ignored for the tests only: `S101` (`assert`), `S311` (the seeded random numbers in the oracle test), `S603` and `S607` (starting the command line in a subprocess). The only `# noqa` comments are in the harness, none in the source or the tests.

Before the freeze, the lint gate was run on the tests while they were still unfrozen. It found many style issues, which were fixed before the tag. This was not a formal run, and it was not recorded.

## 3. Harness runs and outcomes

| Run | Verdict | lint | security | secrets | tests | traceability | integrity |
|---|---|---|---|---|---|---|---|
| run-1 | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS |
| run-2 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

In run 1, 1,193 test cases passed and branch coverage was 96.53%. The only failure was lint: 12 findings, all `I001` (import block not sorted), in 12 test files.

In run 2, all six gates passed, with the same 1,193 tests and the same coverage.

Evidence: `evidence/harness-results/run-1/` and `run-2/`.

## 4. Failure evidence given to the agent

The agent received `evidence/harness-results/run-1/feedback.json`, unedited. For the failed gate it contained the command, the exit status and the 12 failures. Each failure has the rule (`I001`), the file, the line and the message. Only harness evidence was given to the agent.

The 12 files were `tests/helpers.py`, `tests/integration/test_cli.py`, `tests/oracle/test_totals_oracle.py`, `tests/property/test_invariants.py`, and eight files under `tests/unit/` (`test_add`, `test_budgets`, `test_edit_delete`, `test_list`, `test_money`, `test_rules`, `test_storage` and `test_totals`).

## 5. Repair and re-validation

**Cause.** When the test imports were first tidied, `src/expense_tracker/` held only `__init__.py`, so Ruff sorted `expense_tracker.errors` and `expense_tracker.models` as third-party. Once the real modules existed, Ruff treated them as first-party and wanted them in a separate block.

The failure was in the frozen tests, not in the source, so the fix was made through a recorded amendment (A1, `specs/001-expense-tracker/amendments.md`).

**What changed**
- The import order in the 12 test files.
- The integrity gate now follows the newest baseline tag, so that a recorded amendment can move the baseline forward.

**What did not change:** the source code, `spec.md`, `pyproject.toml`, the thresholds, the Ruff rules and the test content.

**Data**
- Commit `1bc74d5`, with the new tag `baseline-1a-before-implement-v2` (annotation `test_functions=81 amendment=A1`). The earlier tag was not moved.
- The tests were not weakened. A script took each of the 12 files, removed the import lines and the blank lines, and compared the result with the baseline version: 12 files changed and 0 differ.
- The source is identical: `evidence/initial-generation/` equals `evidence/final-generation/`.

The same six gates passed in run 2. This was a minor fix. No check was weakened and no guardrail was removed.

## 6. Final human decision, known limitations and justification

**Decision: ACCEPT.**

**Justification**
- Run 1 failed because of a lint finding in the test files, not because of the code. The failure was recorded and fixed without weakening any check.
- Every acceptance criterion is cited by at least one test.

**Known limitations**
- Coverage is not a good measure of test quality. Mutation testing was not done, so a fault could go undetected.
- `__main__.py` shows 0% coverage, because only the subprocess tests run it and coverage does not follow subprocesses. A few other lines are uncovered: four in `cli.py`, three in `storage.py`, and one branch.
- The tests were written by the same agent that wrote the code. They are independent in process (frozen in advance, a separate harness, and an SQLite check), but not in authorship.
- There is no file locking, so if two processes write the file at the same moment, one update can be lost.
- Testing was done only on macOS, not on Windows.
- A few limits were chosen by design and are not in the specification. For example, an expense number longer than 18 digits is refused.
