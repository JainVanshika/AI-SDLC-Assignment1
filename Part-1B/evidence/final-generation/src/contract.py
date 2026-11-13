"""The reply check: the one place that says what a valid reply is (INV-01 to INV-06)."""

import re
from datetime import date

CATEGORIES = frozenset({"food", "travel", "bills", "other"})
MISSING_ITEMS = frozenset({"amount", "currency", "date", "single-expense"})
REASONS = frozenset({"not-an-expense", "unsafe-request"})
SHAPES = {
    "log": {"decision", "expense"},
    "clarify": {"decision", "question", "missing"},
    "refuse": {"decision", "reason", "message"},
}
EXPENSE_FIELDS = {"amount", "category", "date", "description"}
_AMOUNT = re.compile(r"[0-9]{1,12}\.[0-9]{2}")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_MAX_PAISE = 1_000_000_000


def _text(value: object, longest: int) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= longest


def _amount_problem(amount: object) -> str | None:
    if not isinstance(amount, str) or not _AMOUNT.fullmatch(amount):
        return f"INV-03: amount must be text with two decimals, got {amount!r}"
    whole, fraction = amount.split(".")
    if not 1 <= int(whole) * 100 + int(fraction) <= _MAX_PAISE:
        return f"INV-03: amount {amount} is outside 0.01 to 10000000.00"
    return None


def _date_problem(value: object) -> str | None:
    if isinstance(value, str) and _DATE.fullmatch(value):
        try:
            date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
        except ValueError:
            pass
        else:
            return None
    return f"INV-04: date must be a real calendar date YYYY-MM-DD, got {value!r}"


def _expense_problems(expense: object) -> list[str]:
    if not isinstance(expense, dict) or set(expense) != EXPENSE_FIELDS:
        return ["INV-02: the expense must have exactly amount, category, date and description"]
    problems = [_amount_problem(expense["amount"]), _date_problem(expense["date"])]
    if expense["category"] not in CATEGORIES:
        problems.append(f"INV-03: unknown category {expense['category']!r}")
    if not _text(expense["description"], 100):
        problems.append("INV-06: description must be text of 1 to 100 characters")
    return [p for p in problems if p]


def check_reply(reply: object, today: str) -> list[str]:
    """Return the violations of the output contract; an empty list means the reply is valid.

    `today` is the reference date of the request. The contract does not depend on it today, but
    it is part of the call so that a rule about the date can be added without changing callers.
    """
    if not isinstance(reply, dict) or reply.get("decision") not in SHAPES:
        return ["INV-01: the reply must be an object whose decision is log, clarify or refuse"]
    decision = reply["decision"]
    problems = []
    if set(reply) != SHAPES[decision]:
        problems.append(f"INV-02: a {decision} reply must have exactly {sorted(SHAPES[decision])}")
    if decision == "log" and "expense" in reply:
        problems += _expense_problems(reply["expense"])
    if decision == "clarify":
        missing = reply.get("missing")
        if not (isinstance(missing, list) and missing and set(missing) <= MISSING_ITEMS):
            problems.append("INV-05: missing must be a non-empty list of allowed items")
        if not _text(reply.get("question"), 300):
            problems.append("INV-06: question must be text of 1 to 300 characters")
    if decision == "refuse":
        if reply.get("reason") not in REASONS:
            problems.append("INV-05: reason must be not-an-expense or unsafe-request")
        if not _text(reply.get("message"), 300):
            problems.append("INV-06: message must be text of 1 to 300 characters")
    return problems
