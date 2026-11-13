# Analysis: spec, plan and tasks

A read-only cross-check of `spec.md`, `plan.md` and `tasks.md` before implementation, with the constitution as the standard.

## Checks run

| Check | Result |
|---|---|
| Every FR (23) is cited by at least one task | pass |
| Every AC (49) is cited by at least one test task | pass |
| Every FR has an acceptance criterion | pass |
| Every plan module has a task that creates it | pass (`errors`, `money`, `rules`, `models`, `ops`, `storage`, `render`, `cli`) |
| The six harness gates in the plan (R7) are the six gate tasks (T005 to T010) | pass |
| Constitution Principle IV: tests and harness are frozen before `src/` is written | pass (T022 comes before T023) |
| Open `[NEEDS CLARIFICATION]` markers | none |

## Findings

| ID | Severity | Where | Finding | Resolution |
|---|---|---|---|---|
| A1 | Medium | T001 | The Ruff rule set `S` flags `assert` (S101) and subprocess calls (S603, S607) in the tests, so the lint gate would fail for a reason that is not a defect | per-file ignores for `tests/*` only, written into T001 and to be disclosed in the harness log |
| A2 | Low | T003 | The helper starts `python -m expense_tracker.cli`, but T031 creates `__main__.py` so the module to run is `expense_tracker` | T003 changed to `python -m expense_tracker` |
| A3 | Low | T021 | The determinism test forbade imports of `time` and `random` but not calls such as `date.today()` or `datetime.now()`, which are the real ways the clock could be read through `datetime` | T021 now also forbids those two calls |

## Constitution alignment

No conflict. Principle I is covered by T011 and T021, II by T023 to T031, III by T009, IV by T010 and T022, V by T007, T018 and T029.

## Result

No critical or high findings. The three findings above are fixed in `tasks.md`. Ready for the harness and tests.
