# Tasks: Expense and Budget Tracker

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Format: `- [ ] ID [P] Description with file path. Cites: requirements.` `[P]` means it can run beside other `[P]` tasks (different files, no dependency). The order follows the constitution: the harness and the tests are written and frozen under a Git tag (Phase 2) before any code under `src/` is written (Phase 3).

## Phase 1: Setup

- [ ] T001 Create `Part-1A/pyproject.toml`: project `expense-tracker`, `requires-python = ">=3.12,<3.13"`, no run-time dependencies, dev group with pytest, pytest-cov, ruff and bandit, the script `expense = "expense_tracker.cli:main"`, the `ac` pytest marker, `[tool.coverage.run] branch = true, source = ["src/expense_tracker"]`, `[tool.coverage.report] fail_under = 90`, and Ruff rules `select = ["E", "F", "I", "B", "UP", "S", "C90"]`, with `[tool.ruff.lint.per-file-ignores] "tests/*" = ["S101", "S603", "S607"]` because tests use `assert` and start the command line in a subprocess (the ignore is for tests only and is documented in the harness log). Cites: constitution (Standards), plan.
- [ ] T002 Create the empty package `Part-1A/src/expense_tracker/__init__.py` and the folders `tests/unit`, `tests/integration`, `tests/property`, `tests/oracle`, `evidence/initial-generation`, `evidence/final-generation`, `evidence/harness-results`. Cites: plan (Structure).
- [ ] T003 Create `Part-1A/tests/conftest.py` with the `ac` marker and a fixture `run` that calls the command line `main(argv)` in this process, and a helper `run_cli(args, cwd)` that starts `python -m expense_tracker` in a subprocess. Most command line tests use the in-process fixture so that coverage counts them. Cites: constitution III.

## Phase 2: Harness and tests (frozen before implementation)

- [ ] T004 [P] Write `Part-1A/.harness/run_harness.py`: runs the gates in order as separate processes, never imports `expense_tracker`, writes `<gate>.result.json`, the captured output, `feedback.json` for failed gates (command, exit status, output tail, rule or test that failed) and `summary.txt` into `evidence/harness-results/<run-id>/`, and prints one line per gate and a final `PASS` or `FAIL`. Cites: constitution IV, SC-006.
- [ ] T005 [P] Write `Part-1A/.harness/gates/lint.py`: runs `ruff check src tests --no-cache`; passes only with no findings. Cites: constitution (Standards).
- [ ] T006 [P] Write `Part-1A/.harness/gates/security.py`: runs `bandit -r src -ll`; passes only with no medium or high finding. Cites: constitution (Standards).
- [ ] T007 [P] Write `Part-1A/.harness/gates/secrets.py`: runs `gitleaks git` over the history and `gitleaks dir` over the tracked files, no allowlist; passes only with no leak. Cites: constitution V, SC-006.
- [ ] T008 [P] Write `Part-1A/.harness/gates/tests.py`: runs `pytest tests --cov=src/expense_tracker --cov-branch --cov-fail-under=90`; passes only when all tests pass and coverage is at least 90%. Cites: SC-001, SC-005.
- [ ] T009 [P] Write `Part-1A/.harness/gates/traceability.py`: reads every `AC-nnn` of `spec.md` and every `@pytest.mark.ac("AC-nnn")` in `tests/`; fails if an AC has no test or a test cites an unknown AC. Cites: SC-001, constitution III.
- [ ] T010 [P] Write `Part-1A/.harness/gates/integrity.py`: fails if any file under `tests/`, `.harness/`, `specs/001-expense-tracker/spec.md` or `pyproject.toml` differs from the Git tag `baseline-1a-before-implement`, or if the tag does not exist. Cites: constitution IV.
- [ ] T011 [P] [US1] Write `Part-1A/tests/unit/test_money.py`: the accepted and refused amounts. Cites: AC-003, AC-004, FR-002, FR-003.
- [ ] T012 [P] [US1] Write `Part-1A/tests/unit/test_rules.py`: category, date, month, description and id rules. Cites: AC-005, AC-006, AC-007, AC-016, AC-020, AC-033, FR-004 to FR-006, FR-010, FR-016.
- [ ] T013 [P] [US1] Write `Part-1A/tests/unit/test_add.py` using the reference data of the specification. Cites: AC-001, AC-002, AC-008, AC-009, AC-045, FR-001, FR-007.
- [ ] T014 [P] [US1, US2] Write `Part-1A/tests/unit/test_list.py`: ordering, category and month filters, empty results. Cites: AC-010 to AC-015, FR-008 to FR-010.
- [ ] T015 [P] [US3] Write `Part-1A/tests/unit/test_totals.py`. Cites: AC-017, AC-018, AC-019, FR-011.
- [ ] T016 [P] [US4] Write `Part-1A/tests/unit/test_budgets.py`: set, replace, remove, status, warning at, below and above the limit, other month, edit warning. Cites: AC-021 to AC-028, AC-048, AC-049, FR-012 to FR-014, FR-023.
- [ ] T017 [P] [US5] Write `Part-1A/tests/unit/test_edit_delete.py`. Cites: AC-029 to AC-032, AC-034, AC-035, FR-015, FR-016.
- [ ] T018 [P] [US6] Write `Part-1A/tests/unit/test_storage.py` with a temporary folder: round trip, missing file, invalid JSON, bad types, failed write. Cites: AC-036 to AC-040, FR-017 to FR-019.
- [ ] T019 [P] [US7] Write `Part-1A/tests/integration/test_cli.py` with `run_cli`: every command, text and JSON output, exit codes, `--yes`, the default file. Cites: AC-041 to AC-044, AC-046, AC-047, FR-016, FR-017, FR-020, FR-021.
- [ ] T020 [P] Write `Part-1A/tests/oracle/test_totals_oracle.py`: 1,000 stores from `random.Random(seed)`, totals and budget overruns compared with an in-memory SQLite integer computation. Cites: SC-002, FR-011, FR-013.
- [ ] T021 [P] Write `Part-1A/tests/property/test_invariants.py`: no `float` in stored data; same input twice gives the same output; the source never imports `time`, `random`, `socket` or `urllib` and never calls `date.today` or `datetime.now`; 10,000 expenses list and total in under 2 seconds. Cites: FR-022, SC-003.
- [ ] T022 Commit the harness and the tests, then create the annotated tag `baseline-1a-before-implement` with the message `test_functions=<count>`. Nothing under `tests/` or `.harness/` changes after this tag without a recorded amendment. Cites: constitution IV.

## Phase 3: Implementation

- [ ] T023 [P] Create `Part-1A/src/expense_tracker/errors.py`: `ExpenseError(code, message, field)`. Cites: FR-007, FR-021.
- [ ] T024 [P] Create `Part-1A/src/expense_tracker/money.py`: `parse_amount`, `format_rupees`, integer arithmetic only. Cites: FR-002, FR-003, FR-020.
- [ ] T025 [P] Create `Part-1A/src/expense_tracker/rules.py`: category, date, month, description and id checks. Cites: FR-004 to FR-006, FR-010, FR-016.
- [ ] T026 [P] Create `Part-1A/src/expense_tracker/models.py`: frozen `Expense`, `Store`, `Warning`, `Outcome`. Cites: data model.
- [ ] T027 [US1, US2, US3] Create `Part-1A/src/expense_tracker/ops.py` part 1: `add_expense`, `list_expenses`, `monthly_totals`. Cites: FR-001, FR-007 to FR-011.
- [ ] T028 [US4, US5] Extend `ops.py`: `edit_expense`, `delete_expense`, `set_budget`, `remove_budget`, `budget_status` and the budget warning. Cites: FR-012 to FR-016, FR-023.
- [ ] T029 [US6] Create `Part-1A/src/expense_tracker/storage.py`: strict `load`, atomic `save`. Cites: FR-017 to FR-019.
- [ ] T030 [US7] Create `Part-1A/src/expense_tracker/render.py`: text and JSON output. Cites: FR-020.
- [ ] T031 [US7] Create `Part-1A/src/expense_tracker/cli.py` and `__main__.py`: `main(argv) -> int`, exit codes 0, 2, 3, errors on standard error. Cites: FR-020, FR-021, FR-016.

## Phase 4: Evidence and review

- [ ] T032 Copy `src/expense_tracker/` unchanged to `evidence/initial-generation/` before the first harness run. Cites: constitution (Workflow).
- [ ] T033 Run `uv run python .harness/run_harness.py` and keep the output as `evidence/harness-results/run-1/`. Cites: SC-001 to SC-007.
- [ ] T034 If a gate fails, give the agent that run's `feedback.json`, repair `src/` only, and re-run; keep every run. A failure is never created on purpose. Cites: constitution (Workflow).
- [ ] T035 Copy the accepted `src/expense_tracker/` to `evidence/final-generation/`. Cites: constitution (Workflow).
- [ ] T036 Write `Part-1A/evidence/harness-log.md`: the first generation, each run and result, the failure evidence given to the agent, what changed, the final ACCEPT or REJECT decision, limitations. Cites: constitution (Workflow).
- [ ] T037 Write `Part-1A/README.md`: install, run, harness. Cites: quickstart.

## Dependencies

- T001 to T003, then T004 to T021 (all `[P]`, they touch different files), then T022.
- T023 to T026 may start only after T022. T027 needs T023 to T026. T028 needs T027. T029 needs T023 and T026. T030 needs T024. T031 needs T027 to T030.
- T032 follows T031; T033 follows T032; T034 only if T033 fails; T035 to T037 follow acceptance.

## Strategy

Tests and harness first, frozen; then the code in dependency order; the first generation is kept before the harness runs. User stories are delivered in priority order: US1 to US3 (P1) from T027, US4 to US6 (P2) from T028 and T029, US7 (P3) from T030 and T031.
