# Contract: command line and reply

## Command line

```text
expense-logger "<request text>" --today YYYY-MM-DD
expense-logger --info
```

The key is read from `GEMINI_API_KEY`. With uv: `uv run --env-file .env expense-logger "..." --today 2026-11-14`.

## Output

One line of JSON on standard output:

| Case | Shape | Exit |
|---|---|---|
| an answer | `{"model_calls": 1, "reply": {...}}` | 0 |
| an error | `{"model_calls": 0, "error": {"code": "empty-request", "message": "..."}}` | 2 |

Error codes: `empty-request`, `request-too-long`, `invalid-reference-date`, `missing-api-key` (no model call), and `model-unavailable`, `reply-not-json`, `invalid-reply` (after at least one call).

## Reply shapes

```json
{"decision": "log", "expense": {"amount": "450.00", "category": "food", "date": "2026-11-13", "description": "lunch"}}
{"decision": "clarify", "question": "How much did you pay for lunch?", "missing": ["amount"]}
{"decision": "refuse", "reason": "not-an-expense", "message": "I can only log expenses."}
```

Closed vocabularies: `category` in `food`, `travel`, `bills`, `other`; `missing` items in `amount`, `currency`, `date`, `single-expense`; `reason` in `not-an-expense`, `unsafe-request`. Rules INV-01 to INV-06 of the specification apply.

## `--info`

```json
{"model": "gemini-3.5-flash-lite", "temperature": 0, "response_mime_type": "application/json", "timeout_seconds": 60, "max_retries": 3, "max_text_length": 1000, "prompt_sha256": "<hash>"}
```
