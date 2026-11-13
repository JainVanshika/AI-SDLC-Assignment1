# Expense Logger Constitution

## Core Principles

### I. Exact Money, Never Guessed (NON-NEGOTIABLE)
An amount in a reply MUST be rupees written as text with exactly two decimals (`"450.00"`), more
than 0 and at most `"10000000.00"`. The assistant MUST NOT invent an amount, a date or a
category that the request does not state or plainly imply; when the amount is missing or
unusable it MUST ask. Floating-point numbers MUST NOT be used for money anywhere in the code.
Rationale: a wrong amount in a financial record is worse than a question.

### II. The Model Proposes, the Application Decides
The model's reply is untrusted input. The application MUST accept a reply only if it passes the
reply check in full; anything else is reported as an error and never shown as an answer. The
application MUST NOT read the clock: the reference date is always given by the caller.
Rationale: model output varies, so the rules are enforced in code that can be tested exactly.

### III. Specified Behaviour, Testable Without Exact Wording
The specification MUST define the reply contract, the structural invariants, the behavioural
properties, the guardrail rules, the pass threshold and how the score is calculated, before the
application is built. Every requirement and acceptance criterion has an ID, every evaluation case
cites the criteria it covers, and every check compares structure, properties or exact fields, and
never the model's wording.
Rationale: a non-deterministic application can only be judged by checks that allow wording to vary.

### IV. Independent Harness, Never Weakened
The evaluation harness MUST run the application as a separate process and MUST NOT import it.
The harness, the dataset, the tests and the thresholds MUST be written and frozen under a Git tag
before the application is implemented. No case, check, threshold or lint rule MAY be weakened,
removed or disabled to obtain a PASS. A change to any of them MUST be made through the
specification and recorded as an amendment.
Rationale: a harness that can be edited to pass proves nothing.

### V. Safe by Default
The API key MUST come only from the environment (a local `.env` file that Git ignores) and MUST NOT
appear in code, tests, logs, results or commits. Requests used in tests and evaluation MUST be
made up, because the free tier of the model service may use prompts. Text the user types MUST be
treated as data: an instruction inside it MUST NOT change what the assistant does.
Rationale: a leaked key or a followed injected instruction cannot be undone.

## Technology and Quality Standards

- Language and tools: Python 3.12 with uv; pytest; Ruff; Bandit; gitleaks. The model service is
  Google Gemini, model `gemini-3.5-flash-lite`, called with temperature 0 and JSON output.
- Run-time dependencies: the standard library only.
- Measurable gates for an ACCEPT:
  - Ruff reports no findings, with its cache disabled; Bandit reports no medium or high finding;
    gitleaks finds no secret in the Git history or in any file.
  - Every pytest test passes, with branch coverage of at least 90% of the application code.
  - Every acceptance criterion is cited by at least one test or evaluation case.
  - The evaluation run reaches an overall score of at least 0.85, every guardrail case scores
    exactly 1.0, and the structural checks pass on every repetition.
- Model or service failures MUST be recorded separately from wrong answers.

## Development Workflow

- The Spec Kit flow is followed in order: constitution, specify, clarify, plan, tasks, analyze,
  implement. Each stage is committed on its own, with a message of the form `ID : message`.
- The first generated implementation MUST be saved unchanged in `evidence/initial-generation/`
  before the first evaluation. Every evaluation run is kept, and none is overwritten.
- A repair is made by giving the coding agent the failure evidence of a run, and is recorded with
  what failed, what changed and whether the same checks then passed. A failure is never created
  on purpose, and the same cases that guide a repair are not the only evidence of success.
- The final ACCEPT or REJECT decision is made by a person after the evaluation result.

## Governance

This constitution overrides other practices. An amendment MUST be written down, say what changed
and why, and update the version. Versions follow MAJOR.MINOR.PATCH: MAJOR for a removed or
redefined principle, MINOR for a new principle or materially expanded rule, PATCH for wording
fixes. Every plan and every review MUST check compliance with these principles, and any
deviation MUST be justified in the plan.

**Version**: 1.0.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-14
