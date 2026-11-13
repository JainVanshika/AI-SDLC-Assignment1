# Tasks: Natural-Language Expense Logger

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Format: `- [ ] ID [P] Description with file path. Cites: requirements.` `[P]` means it can run beside other `[P]` tasks. The order follows the constitution: the harness, the dataset and the tests are written and frozen under a Git tag (Phase 2) before any code under `src/` is written (Phase 3).

## Phase 1: Setup

- [X] T001 Create `Part-1B/pyproject.toml`: project `expense-logger`, Python `>=3.12,<3.13`, no run-time dependencies, dev group (pytest, pytest-cov, ruff, bandit), the script `expense-logger = "expense_logger.cli:main"`, the `ac` marker, coverage with `branch = true`, `source = ["src/expense_logger"]`, `fail_under = 90`, and Ruff rules `["E", "F", "I", "B", "UP", "S", "C90"]` with per-file ignores for `tests/*` (`S101`, `S311`, `S603`, `S607`). Cites: constitution (Standards).
- [X] T002 Create the package `Part-1B/src/expense_logger/__init__.py`, the folders `prompts`, `evals`, `tests`, `evidence/initial-generation`, `evidence/final-generation`, `evidence/eval-runs`, and `.env.example` with `GEMINI_API_KEY=`. Make sure `.env` is ignored by Git. Cites: FR-016.
- [X] T003 Create `Part-1B/tests/conftest.py` with the `ac` marker and a `FakeClient` that returns a prepared text, or raises a prepared error, and counts its calls. Cites: constitution III.

## Phase 2: Harness, dataset and tests (frozen before implementation)

- [X] T004 [P] Write `Part-1B/.harness/threshold.json`: overall minimum 0.85, guardrail minimum 1.0, repetitions 3, pause 3 seconds, call timeout, the score weights of the specification and the marker phrase. Cites: FR-021, AC-040.
- [X] T005 [P] Write `Part-1B/.harness/layers/structure.py`: INV-01 to INV-06, written independently of the application. Cites: FR-020, AC-020, AC-024, AC-041.
- [X] T006 [P] Write `Part-1B/.harness/layers/properties.py`: PROP-01 to PROP-08. Cites: FR-020, AC-027, AC-041.
- [X] T007 [P] Write `Part-1B/.harness/layers/semantic.py` and `scoring.py`: the layer 3 comparison and the score of the specification, and the verdict rule. Cites: FR-020, FR-021, AC-040.
- [X] T008 [P] Write `Part-1B/.harness/prechecks.py`: lint (Ruff, no cache), security (Bandit, medium and high), tests (pytest with branch coverage at least 90%), secrets (gitleaks over history and files, no allowlist), traceability (every AC is cited by a test or a dataset case) and integrity (the frozen files match the newest baseline tag). Cites: FR-018, constitution (Standards).
- [X] T009 Write `Part-1B/.harness/run_eval.py`: runs the pre-checks, then every case three times by starting `python -m expense_logger` as a subprocess with the key in its environment, pauses 3 seconds between calls, applies the three layers, writes `eval-results.json`, a summary and `feedback.json` to `evidence/eval-runs/<run-id>/`, and never imports the application. Cites: FR-018, FR-022, FR-023, AC-038, AC-042, AC-043.
- [X] T010 [P] Write `Part-1B/evals/dataset.json`: 35 made-up cases with the fields of FR-019, 8 or more guardrail cases, the reference date 2026-11-14. Cites: FR-019, AC-001 to AC-032, AC-046, FR-024.
- [X] T011 [P] Write `Part-1B/tests/test_harness_layers.py`: made-up faulty replies (extra field, invented amount, leaked key, wrong decision, no answer, bad date) flagged by the check that should flag them, and a good reply that passes. Cites: AC-041, AC-020, AC-024, AC-027.
- [X] T012 [P] Write `Part-1B/tests/test_scoring.py`: the score of each ground truth type and the verdict rule. Cites: AC-040, FR-021.
- [X] T013 [P] Write `Part-1B/tests/test_dataset.py`: the shape of the dataset, at least 32 cases, 8 guardrail cases, every case cites known ACs, no email or phone-like number. Cites: AC-039, AC-045, FR-024.
- [X] T014 [P] Write `Part-1B/tests/test_contract.py`: the reply check for each INV with good and bad replies. Cites: AC-008, AC-020, AC-024, AC-034, FR-014.
- [X] T015 [P] Write `Part-1B/tests/test_assistant.py` with the fake client: each error code, no model call for unusable input, the message sent to the model, replies passed through. Cites: AC-030, AC-031, AC-032, AC-034, AC-037, AC-044, FR-012, FR-014.
- [X] T016 [P] Write `Part-1B/tests/test_model.py` with a fake HTTPS connection: request body (temperature 0, JSON output), the key only in the header, retries and waits (a fake `sleep` records the waits instead of waiting), `Retry-After`, timeout, `model-unavailable`. Cites: AC-033, AC-035, FR-013, FR-016.
- [X] T017 [P] Write `Part-1B/tests/test_cli.py`: `--info`, exit codes, one line of JSON, the key never printed. Cites: AC-036, AC-044, AC-027, FR-015, FR-017.
- [X] T018 Commit the harness, the dataset and the tests, then create the annotated tag `baseline-1b-before-implement` with `test_functions=<count> dataset_cases=<count>`. Nothing under `tests/`, `.harness/`, `evals/` or `pyproject.toml` changes after it without a recorded amendment. Cites: constitution IV.

## Phase 3: Implementation

- [X] T019 [P] Create `Part-1B/src/expense_logger/config.py`: limits, model name, retry waits, the paths. Cites: FR-012, FR-013.
- [X] T020 [P] Create `Part-1B/src/expense_logger/contract.py`: `check_reply(reply, today)` that returns the list of violations of INV-01 to INV-06. Cites: FR-001, FR-014.
- [X] T021 [P] Create `Part-1B/src/expense_logger/model.py`: `GeminiClient.generate(system, user)` over `http.client`, with the retry rule, and `ModelUnavailable`. The connection factory and the `sleep` function are parameters, so that tests can replace them. Cites: FR-013, FR-016.
- [X] T022 Create `Part-1B/prompts/system.md`: output contract, ask rules, refuse rules, date rules, category rules, injection rule, and the marker phrase. Cites: FR-002 to FR-011.
- [X] T023 Create `Part-1B/src/expense_logger/assistant.py`: `handle(text, today, client)`. Cites: FR-001, FR-012, FR-014, FR-015.
- [X] T024 Create `Part-1B/src/expense_logger/cli.py` and `__main__.py`: arguments, `--info`, the one-line JSON and exit codes. Cites: FR-015, FR-016, FR-017.

## Phase 4: Evidence and review

- [X] T025 Copy `src/expense_logger/` and `prompts/` unchanged to `evidence/initial-generation/` before the first evaluation. Cites: constitution (Workflow).
- [X] T026 Run the evaluation and keep each run as `evidence/eval-runs/run-N/`. Cites: SC-002, SC-003.
- [X] T027 If a run fails, give the agent that run's `feedback.json`, repair, and run again; keep every run. A failure is never created on purpose. Cites: constitution (Workflow). Not needed: run 1 passed.
- [X] T028 Copy the accepted `src/` and `prompts/` to `evidence/final-generation/`. Cites: constitution (Workflow).
- [X] T029 Write and run `evidence/fresh-check/run_fresh_check.py` on at least 12 new requests, once, with no pass mark. Cites: SC-007.
- [ ] T030 Write `Part-1B/evidence/harness-log.md`. Cites: constitution (Workflow).
- [X] T031 Write `Part-1B/README.md`. Cites: quickstart.

## Dependencies

T001 to T003, then T004 to T017 (`[P]`, different files; T009 needs T004 to T008), then T018. T019 to T022 only after T018; T023 needs T019 to T022; T024 needs T023. T025 follows T024; T026 follows T025; T027 only if T026 fails; T028 to T031 follow acceptance.
