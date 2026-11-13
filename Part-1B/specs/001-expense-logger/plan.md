# Implementation Plan: Natural-Language Expense Logger

**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-expense-logger/spec.md`

## Summary

A small command-line program that sends one request text and a reference date to Google Gemini, checks the model's JSON reply against the output contract in code, and prints one line of JSON: the reply or an error. A separate evaluation harness runs the program as a subprocess on a dataset of made-up requests, three times each, and judges every answer in three layers (structure, properties, comparison with the ground truth) without a model as judge. The assistant extracts the expense only; it does not store it.

## Technical Context

**Language/Version**: Python 3.12 (`requires-python >=3.12,<3.13`), managed with uv

**Primary Dependencies**: none at run time (standard library: `http.client`, `json`, `re`, `datetime`, `hashlib`, `argparse`, `os`)

**Development tools**: pytest, pytest-cov, Ruff, Bandit; gitleaks as an external program

**Model service**: Google Gemini, model `gemini-3.5-flash-lite`, temperature 0, JSON output, key in `GEMINI_API_KEY`

**Storage**: none; results of evaluation runs are JSON files under `evidence/eval-runs/`

**Testing**: pytest with a fake model service for the application; the harness layers are tested on made-up replies

**Project Type**: command-line program and evaluation harness

**Performance Goals**: a full evaluation run (about 35 cases, three repetitions) in under 15 minutes with a 3-second pause between calls

**Constraints**: no clock, no floating-point money, key only from the environment, made-up requests only

**Scale/Scope**: one request at a time, three decisions, four categories

## Constitution Check

| Principle | How the design satisfies it |
|---|---|
| I. Exact Money, Never Guessed | the reply check requires amount text with two decimals in range; the prompt forbids guessing; PROP-03 checks that the digits come from the request |
| II. The Model Proposes, the Application Decides | `contract.check_reply` rejects any invalid reply as `invalid-reply`; the reference date comes from the caller |
| III. Specified Behaviour, Testable Without Wording | INV, PROP and score rules are in the spec; the dataset cites AC IDs; wording fields are never compared |
| IV. Independent Harness, Never Weakened | the harness runs `python -m expense_logger` as a subprocess and holds its own copy of the rules; tests, harness, dataset and thresholds are frozen under a Git tag |
| V. Safe by Default | the key is read from the environment, sent in a header only, and the harness never prints it; every request is made up; the user text is passed as delimited data |

No violations.

## Key Decisions

- **D1. JSON mode, no response schema.** The call asks for `application/json` and the contract is enforced by `contract.check_reply` in code. One place defines what is valid, and a malformed reply becomes a counted `invalid-reply` and is never shown (FR-014).
- **D2. Request layout.** The system prompt is fixed text (so its SHA-256 identifies it). The user message is `Reference date: YYYY-MM-DD` and then the request text between `<request>` and `</request>`, so the text is data (FR-010).
- **D3. Transport.** `http.client` over HTTPS, so there is no run-time dependency and no `urllib` security warning. The key goes only in the `x-goog-api-key` header (FR-016).
- **D4. Retry rule.** 429, 5xx and timeouts are retried up to 3 times after 5, 15 and 45 seconds or the `Retry-After` value; other failures are not retried. An invalid reply is not retried (FR-013, FR-014).
- **D5. Errors.** `empty-request`, `request-too-long`, `invalid-reference-date`, `missing-api-key` stop before any model call; `model-unavailable`, `reply-not-json`, `invalid-reply` come after. Exit 0 for an answer (including `clarify` and `refuse`), 2 for an error (FR-015).
- **D6. Harness independence.** The harness reads `.env` itself and passes the key to the child process; it never imports `expense_logger` and holds its own copy of the rules.
- **D7. Evaluation.** 35 made-up cases in `evals/dataset.json`; three repetitions; 3 seconds between calls; per-repetition results, scores and a verdict; `feedback.json` for failed cases (FR-018 to FR-023).
- **D8. Held-out check.** A separate script runs at least 12 new requests once, with no pass mark, to see whether repairs generalise (SC-007).

## Requirement Map

| Requirement | Module |
|---|---|
| FR-001, FR-014, FR-020 (layer 1) | `contract.py` |
| FR-002 to FR-011 | `prompts/system.md` (the model's behaviour), checked by the dataset |
| FR-012, FR-015, FR-016, FR-017 | `assistant.py`, `cli.py` |
| FR-013 | `model.py` |
| FR-018 to FR-023 | `.harness/` |
| FR-024 | the dataset and a test over it |

## Project Structure

```text
specs/001-expense-logger/
├── spec.md  plan.md  research.md  quickstart.md  tasks.md  analysis.md
├── contracts/reply.md
└── checklists/requirements.md

src/expense_logger/
├── __init__.py  __main__.py
├── config.py      # limits, model name, retry waits
├── contract.py    # check_reply: the reply check
├── model.py       # GeminiClient with retries, ModelUnavailable
├── assistant.py   # handle(text, today, client)
└── cli.py         # main(argv)
prompts/system.md  # the system prompt, with the marker phrase
evals/dataset.json # the made-up cases and their ground truth
.harness/          # run_eval.py, prechecks, layers/, scoring, threshold.json
tests/             # unit tests, harness tests
evidence/          # initial-generation/, final-generation/, eval-runs/, fresh-check/, harness-log.md
```

**Structure Decision**: one small package plus a separate harness folder that does not import it (Principle IV).
