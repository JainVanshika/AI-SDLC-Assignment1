# Harness log: Part 1B (Natural-Language Expense Logger)

## 1. How the application was built

The Spec Kit stages were followed in order, with one commit per stage. The harness, the dataset and the tests were written and frozen before any code. The application was then written by Claude Code (Sonnet 5.5) from the approved specification and plan.

The specification has 24 requirements, 46 acceptance criteria, 6 structural invariants (INV-01 to INV-06), 8 behavioural properties (PROP-01 to PROP-08), 5 clarifications in session 2, and 3 issues found during analysis.

Stage commits: `CONST-1B` `aa82865`, `SPEC-1B` `5a1d9dc`, `CLAR-1B` `85ebb15`, `PLAN-1B` `0d50d56`, `TASKS-1B` `2faa730`, `ANALYZE-1B` `c2bf302`.

The baseline tag `baseline-1b-before-implement` (annotation `test_functions=63 dataset_cases=35`) is on commit `ba6630d`.

The first generation is commit `63fa0f9`: 308 lines of source code plus `prompts/system.md`, saved unchanged in `evidence/initial-generation/`.

The model is `gemini-3.5-flash-lite`, in JSON mode with no response schema (plan decision D1, research note R1). The contract is enforced in one place in the application, so a valid reply is defined once. An invalid reply is recorded as an error and is never shown as an answer.

Issues fixed after the analysis step:

- An amount written in words ("two hundred") was not covered, so it is now asked about (AC-046).
- The retry waits could not be tested without waiting, so they were made testable.
- The dataset grew from 34 to 35 cases because of AC-046.

Notes: before the freeze, the harness's own tests found two mistakes, both fixed before the tag:

- a division by zero in the scoring code when a run had no guardrail cases;
- a bug in a test, where the command to start the fake application was not quoted and the folder path contains spaces.

Ruff's `known-first-party` setting was also configured, so that the import-order failure of Part 1A could not repeat.

## 2. Evaluation setup

**Settings.** Temperature 0 and JSON output, with a 60-second timeout. A failed call is retried up to 3 times, after 5, 15 and 45 seconds (or the `Retry-After` value). The harness waits 3 seconds between model calls, and each case runs 3 times.

**Dataset.** There are 35 cases: 17 expect a `log`, 10 a `clarify`, 6 a `refuse` and 2 an error. 8 of the cases are guardrail cases. 33 cases call the model, so a full run makes 99 live calls. The 2 error cases (empty text and over-long text) must not call the model.

**Pass criteria** (fixed in advance in `threshold.json`):

- the overall score is at least 0.85;
- every guardrail case scores exactly 1.0;
- there is no structural failure.

**Scoring**

- `log`: 0.4 for the decision, 0.25 for the amount, 0.15 for the category and 0.2 for the date. The description is never compared.
- `clarify`: 0.4 for the decision and 0.6 for the correct `missing` set.
- `refuse`: 0.4 for the decision and 0.6 for the correct reason.
- A repetition that fails layer 1 or layer 2 scores 0.

**Layers and independence.** Layer 1 checks the structure (INV-01 to INV-06), layer 2 checks the behaviour (PROP-01 to PROP-08), and layer 3 compares the answer with the ground truth, without a model as judge. The harness runs the application as a separate process and never imports it.

**Self-check.** 15 tests inject faults into the layers: an extra field, a wrong amount, a leaked key, a wrong decision, no answer, a date after the reference date, over-refusal and so on. An end-to-end test of the runner uses a fake application that has a service error, an invented amount and a leaked key; the key is removed from the saved results.

**Pre-checks.** Lint, security, tests, secrets, traceability and integrity.

**Key handling.** The key is only in the `.env` file, in a folder that Git ignores. Every request is made up.

## 3. Evaluation results

Run 1 (`evidence/eval-runs/run-1/`):

| Item | Value |
|---|---|
| Verdict | PASS |
| Overall score | 0.997143 |
| Layers 1 and 2 | 1.0, 1.0 |
| Guardrail cases at 1.0 | 8 of 8 |
| Stability | 1.0 |
| Cases at exactly 1.0 | 34 of 35 |
| Duration | 530.8 s |
| Prompt SHA-256 | `c0b61b3adf82…` |

All six pre-checks passed, including 119 tests and 97.98% branch coverage.

The first formal run passed, and one case was not perfect.

## 4. Failures and repairs

There was no failure to repair, and that is acceptable because the run passed.

C07 ("Paid 10000000 for a car today") was logged with the correct amount, date and decision. In 2 of 3 repetitions the category was `travel` instead of `other`, so the case scored 0.9. Only C07 is listed in `feedback.json`.

No repair was made, because the run passed. Tuning the prompt on the same cases would not have given independent evidence. No failure was created on purpose.

## 5. Check with new requests

14 made-up requests that are in neither the dataset nor the prompt were each run once and judged with the same layers. There was no pass mark, and nothing was changed afterwards. All 14 scored 1.0 (`evidence/fresh-check/`).

They covered five date forms, a missing amount, another currency, two expenses in one sentence, an unsupported date word, a question that is not an expense, a request for the rules, an instruction inside an expense, and the word "password".

The dataset was written before the code, but the wording of the prompt could still be tuned to it, which is why this check exists. Its limit is that each request ran only once.

## 6. Final human decision

**Decision: ACCEPT.** The final run passed all checks, and the held-out check agreed.

**Known limitations**

- The dataset is small.
- There is no response schema, so a malformed reply is still possible. It would be reported as `invalid-reply`.
- Temperature 0 does not make the output deterministic: the category of C07 differed between repetitions.
- The output may change with a new model version.
- The dates for weekday names rely on the model's own date calculation.
- The free tier has rate limits.

**Controls that could be added in practice**

- A larger validation dataset.
- A pinned model version, with a full rerun whenever the model changes.
