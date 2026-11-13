# Natural-Language Expense Logger (Part 1B)

A command-line assistant that turns one sentence about spending into a structured expense. You type, for example, "Paid 450 for lunch yesterday". Google Gemini decides whether the sentence describes one clear expense (log it), is missing something (ask a question) or is not a request to log an expense (refuse). The assistant only extracts the expense; it does not save it.

```text
$ uv run --env-file .env expense-logger "Paid 450 for lunch yesterday" --today 2026-11-14
{"model_calls": 1, "reply": {"decision": "log", "expense": {"amount": "450.00", "category": "food", "date": "2026-11-13", "description": "lunch"}}}
```

Because a model's answers vary from run to run, the assistant is judged by an evaluation harness that checks structure, behaviour and correctness on a dataset of 35 made-up requests, each run three times, and not by comparing exact wording.

## Install

Python 3.12 and [uv](https://docs.astral.sh/uv/) are needed. From this folder:

```text
uv sync
```

The harness also uses gitleaks to scan for secrets: `brew install gitleaks` on macOS, or see the gitleaks documentation for other platforms.

## The API key

The assistant reads the key from the environment variable `GEMINI_API_KEY`. Create a free key in Google AI Studio and put it in a file named `.env` in this folder, with one line:

```text
GEMINI_API_KEY=<your key>
```

`.env` is ignored by Git and must never be committed; `.env.example` shows the format. The free tier may use prompts to improve Google's products, so use only made-up requests. The key is sent only in a request header and is never printed, logged or written to a result file.

## Use

```text
uv run --env-file .env expense-logger "<request>" --today YYYY-MM-DD
uv run expense-logger --info
```

`--today` is the reference date ("today"). It is required, because the assistant never reads the clock; "yesterday" and "on Monday" are worked out from it.

The answer is one line of JSON: `model_calls`, and either `reply` or `error`. A reply is one of three decisions:

| Decision | Fields | Example request |
|---|---|---|
| `log` | `expense` with `amount` (text, two decimals), `category` (food, travel, bills, other), `date`, `description` | "Paid 450 for lunch yesterday" |
| `clarify` | `question`, `missing` (amount, currency, date, single-expense) | "Bought lunch yesterday" |
| `refuse` | `reason` (not-an-expense, unsafe-request), `message` | "What is the weather today?" |

The exit status is 0 when an answer was produced (including a question and a refusal) and 2 for an application error: `empty-request`, `request-too-long`, `invalid-reference-date`, `missing-api-key`, `model-unavailable`, `reply-not-json` or `invalid-reply`. `--info` prints the model, its settings and the SHA-256 of the system prompt, without a model call and without a key.

Understood dates: today, yesterday, the day before yesterday, "N days ago" (1 to 30), a weekday name (its most recent occurrence before the reference date), and an explicit `YYYY-MM-DD`. Amounts must be written in digits, in rupees, between 0.01 and 10000000.00.

## Tests

```text
uv run pytest tests -q
```

These test the application with a fake model service, and the evaluation harness itself, without the network.

## Evaluation

```text
uv run --env-file .env python .harness/run_eval.py
```

The runner first checks the application code (lint, security scan, tests, secret scan, traceability of the acceptance criteria, and the protected files against the Git tag `baseline-1b-before-implement`), then runs every case in `evals/dataset.json` three times through the command line as a separate process, with a 3-second pause between model calls (about 9 to 12 minutes in all). It judges each answer in three layers, without a model as judge, and gives a verdict by the rule in `.harness/threshold.json`: overall score at least 0.85, every guardrail case exactly 1.0, and no structural failure.

Results are written to `evidence/eval-runs/<run-id>/` (`eval-results.json`, a `summary.txt`, and `feedback.json` when a case scores below 1.0).

## Layout

```text
src/expense_logger/   config, contract (the reply check), model (Gemini with retries), assistant, cli
prompts/system.md     the system prompt
evals/dataset.json    the 35 made-up cases and their ground truth
.harness/             the runner, the three layers, scoring, pre-checks (never imports the application)
tests/                unit tests for the application and the harness
specs/001-expense-logger/   specification, plan, tasks, contract, analysis
evidence/             initial and final generation, evaluation runs, held-out check, harness log
```

## Limits

- Without a response schema, a malformed reply is possible. The application reports it as `invalid-reply` and the evaluation counts it as a failure.
- Temperature 0 reduces variation but does not remove it, and the model may change over time.
- The dataset is small (35 cases) and made up.
- The free tier of the model service has rate limits that are not published; a heavy day can give `model-unavailable`.
