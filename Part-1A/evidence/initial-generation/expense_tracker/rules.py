"""The input rules of the specification, one function per kind of input."""

import re
from datetime import date

from .errors import ExpenseError

CATEGORIES = ("food", "travel", "bills", "other")
MAX_DESCRIPTION = 100
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_MONTH = re.compile(r"[0-9]{4}-(?:0[1-9]|1[0-2])")
_ID = re.compile(r"[1-9][0-9]*")
_MAX_ID_DIGITS = 18


def check_category(value: object) -> str:
    if not isinstance(value, str) or value not in CATEGORIES:
        raise ExpenseError(
            "invalid-category", "category must be one of: " + ", ".join(CATEGORIES), "category"
        )
    return value


def check_date(value: object) -> str:
    if isinstance(value, str) and _DATE.fullmatch(value):
        try:
            date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
        except ValueError:
            pass
        else:
            return value
    raise ExpenseError("invalid-date", "date must be a real calendar date, YYYY-MM-DD", "date")


def check_month(value: object) -> str:
    if not isinstance(value, str) or not _MONTH.fullmatch(value):
        raise ExpenseError("invalid-month", "month must be written YYYY-MM", "month")
    return value


def check_description(value: object) -> str:
    if not isinstance(value, str) or len(value) > MAX_DESCRIPTION:
        raise ExpenseError(
            "invalid-description",
            f"description must be text of at most {MAX_DESCRIPTION} characters",
            "description",
        )
    return value


def check_id(value: object) -> int:
    """An expense number: a whole number of 1 or more, as text or as an integer."""
    if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
        return value
    if isinstance(value, str) and _ID.fullmatch(value) and len(value) <= _MAX_ID_DIGITS:
        return int(value)
    raise ExpenseError("invalid-id", "expense number must be a whole number of 1 or more", "id")
