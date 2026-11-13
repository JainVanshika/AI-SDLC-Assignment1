# Expense Tracker Constitution

## Core Principles

### I. Exact Money (NON-NEGOTIABLE)
Every amount MUST be stored and calculated as a whole number of paise (an integer). Floating-point
numbers MUST NOT be used for money anywhere, including input parsing, totals and budget checks.
The only currency is the Indian rupee (INR). An amount that is zero, negative, not a whole number
of paise or not a number MUST be rejected with a stable error code.
Rationale: float rounding makes totals wrong by a paisa, and a wrong total cannot be tested by an
exact assertion.

### II. Library First, Command Line Second
All behaviour MUST live in a plain library of small functions that do not print, read the clock
or touch the file system, except one storage module that reads and writes the JSON file. The
command line MUST only parse arguments, call the library and print the result. Every function
that depends on "today" MUST take the date as an argument, so the same input always gives the
same output.
Rationale: a deterministic core can be checked by exact tests, and the command line stays thin.

### III. Specified Before Built
Every requirement MUST have an ID (FR-nnn) and every acceptance criterion an ID (AC-nnn) that is
specific enough to become a pass/fail test. Every task MUST cite the requirements it serves and
every test MUST cite the acceptance criterion it checks. Code MUST NOT be written for a behaviour
that the specification does not state.
Rationale: traceability from the specification to the tests is how the work is reviewed.

### IV. Independent Harness, Never Weakened
The harness (lint, security, tests, secret scan) MUST run as a separate program and MUST NOT
import the application. The tests, the harness and the thresholds MUST be written and frozen
under a Git tag before the application is implemented. No acceptance criterion, test, threshold
or lint rule MAY be weakened, removed or disabled to obtain a PASS. A change to any of them MUST
be made through the specification and recorded as an amendment.
Rationale: a check that can be edited to pass proves nothing.

### V. Safe by Default
All input MUST be validated before it is used, and an error MUST name the offending field and
carry a stable code. Secrets, keys and credentials MUST NOT appear in source code, tests, logs,
results or commits. The data file MUST be written so that a failed write cannot leave it half
written.
Rationale: the tool keeps personal financial records, and data loss or a leaked key cannot be
undone.

## Technology and Quality Standards

- Language and tools: Python 3.12, managed with uv; pytest for tests; Ruff for lint; Bandit for
  security analysis; gitleaks for secret scanning.
- Measurable gates, all of which MUST pass for an ACCEPT:
  - Ruff reports no findings, with its cache disabled.
  - Bandit reports no findings of medium or high severity.
  - gitleaks finds no secret in the Git history or in any tracked file.
  - Every pytest test passes, with branch coverage of at least 90% of the library.
  - Every acceptance criterion is checked by at least one test that cites its ID.
- Data: one JSON file on disk. Categories are a fixed list (food, travel, bills, other).
  A category budget is a monthly limit; an expense that would go over it is saved and the result
  carries a warning.
- Dependencies: only the standard library plus the tools above, unless the plan justifies one.

## Development Workflow

- The Spec Kit flow is followed in order: constitution, specify, clarify, plan, tasks, analyze,
  implement. Each stage is committed on its own, with a message of the form `ID : message`.
- The first generated implementation MUST be saved unchanged in `evidence/initial-generation/`
  before any harness-driven repair.
- Repairs are made by giving the coding agent the harness failure output, and each repair is
  recorded with what failed, what changed and whether the same checks then passed.
- A failure MUST NOT be created on purpose. Limitations that remain are disclosed, not hidden.
- The final ACCEPT or REJECT decision is made by a person after the harness result.

## Governance

This constitution overrides other practices. An amendment MUST be written down, say what changed
and why, and update the version. Versions follow MAJOR.MINOR.PATCH: MAJOR for a removed or
redefined principle, MINOR for a new principle or materially expanded rule, PATCH for wording
fixes. Every plan and every review MUST check compliance with these principles, and any
deviation MUST be justified in the plan.

**Version**: 1.0.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-14
