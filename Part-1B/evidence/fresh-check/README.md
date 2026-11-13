# Held-out check

The evaluation dataset is made up and was written before the application, so a good score on it shows how the assistant handles those 35 requests, not how it handles wording it has not been tested on. This folder holds a separate check on 14 made-up requests that are in neither the dataset nor the system prompt.

- `run_fresh_check.py` holds the requests and their expected answers, runs each request once through the real application, and judges it with the harness's three layers. It has no pass mark, and nothing in `src/` or `prompts/` was changed because of its result.
- `results.json` is the run: 14 of 14 requests scored exactly 1.0.
- The requests cover six clear expenses (with "yesterday", "three days ago", an explicit date, a weekday name and the day before yesterday), a missing amount, another currency, two expenses in one sentence, an unsupported date word, a question that is not an expense, a request to reveal the rules, an expense with an instruction inside it, and a harmless request with the word "password".

This is a small sample of one run each at temperature 0, so it is evidence of generalisation and not a measurement of it.
