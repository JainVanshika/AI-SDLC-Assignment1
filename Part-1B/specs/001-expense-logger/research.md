# Research: Natural-Language Expense Logger

## R1. Output format: JSON mode without a response schema

- **Decision**: ask Gemini for `application/json` and enforce the contract in the application with `contract.check_reply`.
- **Reason**: the contract (three shapes, closed vocabularies, amount text with two decimals) lives in one tested place and the same function produces the `invalid-reply` error; a schema in the request would be a second definition that could drift from the first.
- **Alternatives**: a `responseSchema` or `responseJsonSchema` in the request (two definitions; the service's schema dialect limits what can be expressed, such as one object shape per decision); free text with a regular expression (fragile).
- **Risk**: without a schema a malformed reply is possible. It is caught and counted, and listed as a limitation.

## R2. Separating instructions from data

- **Decision**: a fixed system prompt, and a user message that gives the reference date and puts the request text between `<request>` and `</request>`.
- **Reason**: FR-010 needs text inside the request to be treated as data; delimiters and an explicit rule in the prompt are the standard defence, and PROP-06 checks the result.
- **Alternatives**: putting the request in the system prompt (mixes data and instructions).

## R3. Reference date from the caller

- **Decision**: `--today YYYY-MM-DD` is required; a missing or invalid value is `invalid-reference-date`.
- **Reason**: the tool must not read the clock (constitution II), so that the same request gives the same date in every run and the ground truth can be exact.
- **Alternatives**: the computer's date (makes the evaluation depend on the day it is run).

## R4. Scoring without a model as judge

- **Decision**: layer 3 compares the amount, category and date exactly, and compares `missing` and `reason` as sets and strings; wording fields are never compared.
- **Reason**: the fields that matter have one right answer, and the fields that vary (`question`, `message`, `description`) are checked only for shape and length (INV-06).
- **Alternatives**: a second model as judge (adds a second non-deterministic component to the evaluation); string similarity (a threshold with no meaning).

## R5. Transport and retries

- **Decision**: `http.client` with a 60-second timeout and the retry rule of FR-013.
- **Reason**: no dependency, and `urllib` triggers a security-lint warning for opening arbitrary URLs. A free tier can rate-limit, so retries with waits are needed, and a service failure must be recorded apart from a wrong answer (FR-023).
- **Alternatives**: the `google-genai` library (a run-time dependency).

## R6. Harness structure

- **Decision**: the pre-checks (lint, security, tests, secrets, integrity) run before any model call; the evaluation then runs each case three times as a subprocess, with a 3-second pause between calls.
- **Reason**: a broken build should be caught before it uses model quota; a pause keeps the free tier from rate-limiting.
- **Alternatives**: calling the application's functions directly (breaks independence).
