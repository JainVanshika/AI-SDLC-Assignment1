"""Layer 1: the structure of an answer (INV-01 to INV-06), written independently of the application."""

import re
from datetime import date

CATEGORIES = {"food", "travel", "bills", "other"}
MISSING = {"amount", "currency", "date", "single-expense"}
REASONS = {"not-an-expense", "unsafe-request"}
SHAPES = {
    "log": {"decision", "expense"},
    "clarify": {"decision", "question", "missing"},
    "refuse": {"decision", "reason", "message"},
}
EXPENSE_KEYS = {"amount", "category", "date", "description"}
AMOUNT = re.compile(r"[0-9]{1,12}\.[0-9]{2}")
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
MAX_PAISE = 1_000_000_000


def _text_ok(value: object, longest: int) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= longest


def _violation(rule: str, detail: str) -> dict:
    return {"rule": rule, "detail": detail}


def _expense_problems(expense: object) -> list[dict]:
    if not isinstance(expense, dict) or set(expense) != EXPENSE_KEYS:
        return [
            _violation(
                "INV-02", "the expense does not have exactly amount, category, date, description"
            )
        ]
    problems = []
    amount = expense["amount"]
    if not isinstance(amount, str) or not AMOUNT.fullmatch(amount):
        problems.append(_violation("INV-03", f"amount is not text with two decimals: {amount!r}"))
    else:
        whole, fraction = amount.split(".")
        if not 1 <= int(whole) * 100 + int(fraction) <= MAX_PAISE:
            problems.append(_violation("INV-03", f"amount is out of range: {amount}"))
    if expense["category"] not in CATEGORIES:
        problems.append(_violation("INV-03", f"unknown category: {expense['category']!r}"))
    when = expense["date"]
    try:
        if not (isinstance(when, str) and DATE.fullmatch(when)):
            raise ValueError
        date(int(when[0:4]), int(when[5:7]), int(when[8:10]))
    except ValueError:
        problems.append(_violation("INV-04", f"date is not a real calendar date: {when!r}"))
    if not _text_ok(expense["description"], 100):
        problems.append(_violation("INV-06", "description is not text of 1 to 100 characters"))
    return problems


def check(answer: dict, case: dict) -> list[dict]:
    """Return the structural violations of one answer; an empty list means layer 1 is clean."""
    if case["expected"]["decision"] == "error":
        return []  # an expected application error has no reply to check
    if "reply" not in answer:
        error = (answer.get("error") or {}).get("code", "no JSON line")
        return [_violation("INV-01", f"no reply was produced ({error})")]
    reply = answer["reply"]
    if not isinstance(reply, dict) or reply.get("decision") not in SHAPES:
        return [
            _violation("INV-01", "the reply is not an object with decision log, clarify or refuse")
        ]
    problems = []
    decision = reply["decision"]
    if set(reply) != SHAPES[decision]:
        problems.append(
            _violation("INV-02", f"a {decision} reply has the wrong fields: {sorted(reply)}")
        )
    if decision == "log" and "expense" in reply:
        problems += _expense_problems(reply["expense"])
    if decision == "clarify":
        missing = reply.get("missing")
        if not (isinstance(missing, list) and missing and set(missing) <= MISSING):
            problems.append(
                _violation(
                    "INV-05", f"missing is not a non-empty list of allowed items: {missing!r}"
                )
            )
        if not _text_ok(reply.get("question"), 300):
            problems.append(_violation("INV-06", "question is not text of 1 to 300 characters"))
    if decision == "refuse":
        if reply.get("reason") not in REASONS:
            problems.append(_violation("INV-05", f"unknown reason: {reply.get('reason')!r}"))
        if not _text_ok(reply.get("message"), 300):
            problems.append(_violation("INV-06", "message is not text of 1 to 300 characters"))
    return problems
