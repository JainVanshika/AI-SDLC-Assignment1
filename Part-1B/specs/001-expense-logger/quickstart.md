# Quickstart: Natural-Language Expense Logger

Commands run from `Part-1B/`. Use made-up requests only: the free tier of the model service may use prompts.

## Install and key

```text
uv sync
```

Create a file `.env` in this folder with one line, `GEMINI_API_KEY=<your key>`. Git ignores it. Never commit it.

## Try it

```text
uv run expense-logger --info
uv run --env-file .env expense-logger "Paid 450 for lunch yesterday" --today 2026-11-14
```

Expected (AC-001): a `reply` with decision `log`, amount `"450.00"`, category `food`, date `2026-11-13`.

```text
uv run --env-file .env expense-logger "Bought lunch yesterday" --today 2026-11-14
```

Expected (AC-014): decision `clarify` with `missing` equal to `["amount"]`.

```text
uv run --env-file .env expense-logger "What is the weather today?" --today 2026-11-14
```

Expected (AC-021): decision `refuse` with reason `not-an-expense`.

## Run the checks

```text
uv run pytest tests -q
uv run --env-file .env python .harness/run_eval.py
```

The evaluation first runs the pre-checks, then every case three times (about 12 minutes), and writes the run to `evidence/eval-runs/<run-id>/` with a verdict.
