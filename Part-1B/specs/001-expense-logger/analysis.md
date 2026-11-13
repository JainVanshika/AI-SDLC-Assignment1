# Analysis: spec, plan and tasks

A read-only cross-check of `spec.md`, `plan.md` and `tasks.md` before implementation, with the constitution as the standard.

## Checks run

| Check | Result |
|---|---|
| Every FR (24) is cited by at least one task | pass |
| Every AC (46) is cited by at least one task | pass |
| Every FR has an acceptance criterion | pass |
| Every module of the plan has a task that creates it | pass (`config`, `contract`, `model`, `assistant`, `cli`, the system prompt, the harness) |
| Constitution Principle IV: harness, dataset and tests are frozen before `src/` is written | pass (T018 comes before T019) |
| Open `[NEEDS CLARIFICATION]` markers | none |

## Findings

| ID | Severity | Where | Finding | Resolution |
|---|---|---|---|---|
| A1 | Medium | FR-003, edge cases | The specification did not say what happens to an amount written in words ("two hundred"); the model could log it or ask, and PROP-03 (the digits of the amount appear in the request) would flag a logged one as invented | FR-003 and the edge cases now say only digits are read and words are asked about; AC-046 and a dataset case were added |
| A2 | Medium | T016, T021 | The retry waits (5, 15, 45 seconds) cannot be tested without waiting 65 seconds, unless the sleep function and the connection can be replaced | T021 and T016 now make them parameters |
| A3 | Low | plan, T010 | The dataset size grew from 34 to 35 cases with AC-046 | plan, tasks and the checklist changed to 35 |

## Constitution alignment

No conflict. Principle I is covered by T005, T006 and the dataset, II by T020 and T023, III by T004 to T007 and T010, IV by T009 and T018, V by T002, T016 and T017.

## Result

No critical or high findings. The three findings above are fixed. Ready for the harness, the dataset and the tests.
