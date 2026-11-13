"""The data file: a strict loader and an atomic writer. The only module that touches the disk."""

import contextlib
import json
import os
import tempfile
from pathlib import Path

from . import money, rules
from .errors import ExpenseError
from .models import Expense, Store

_FILE_KEYS = {"version", "next_id", "expenses", "budgets"}
_EXPENSE_KEYS = {"id", "amount_paise", "category", "date", "description"}


def _bad(path: Path, why: str) -> ExpenseError:
    return ExpenseError("storage-error", f"{path.name} cannot be used: {why}", None)


def _is_int(value: object) -> bool:
    return type(value) is int  # a bool is an int in Python, so isinstance would let True through


def _amount_ok(value: object) -> bool:
    return _is_int(value) and 1 <= value <= money.MAX_PAISE


def _read_expense(path: Path, item: object) -> Expense:
    if not isinstance(item, dict) or set(item) != _EXPENSE_KEYS:
        raise _bad(path, "an expense does not have exactly the expected fields")
    if not _is_int(item["id"]) or item["id"] < 1:
        raise _bad(path, "an expense number is not a whole number of 1 or more")
    if not _amount_ok(item["amount_paise"]):
        raise _bad(path, "an amount is not a whole number of paise in range")
    try:
        category = rules.check_category(item["category"])
        date = rules.check_date(item["date"])
        description = rules.check_description(item["description"])
    except ExpenseError as error:
        raise _bad(path, f"an expense has an invalid {error.field}") from error
    return Expense(item["id"], item["amount_paise"], category, date, description)


def _read_budgets(path: Path, budgets: object) -> dict[str, int]:
    if not isinstance(budgets, dict):
        raise _bad(path, "budgets is not an object")
    for category, limit in budgets.items():
        if category not in rules.CATEGORIES or not _amount_ok(limit):
            raise _bad(path, "a budget has an unknown category or a limit that is not valid")
    return dict(budgets)


def _parse(path: Path, data: object) -> Store:
    if not isinstance(data, dict) or set(data) != _FILE_KEYS:
        raise _bad(path, "the file does not have exactly the expected fields")
    if not _is_int(data["version"]) or data["version"] != 1:
        raise _bad(path, "the file version is not 1")
    if not isinstance(data["expenses"], list):
        raise _bad(path, "expenses is not a list")
    expenses = tuple(_read_expense(path, item) for item in data["expenses"])
    numbers = [e.id for e in expenses]
    if len(set(numbers)) != len(numbers):
        raise _bad(path, "an expense number is used twice")
    if not _is_int(data["next_id"]) or data["next_id"] <= max(numbers, default=0):
        raise _bad(path, "next_id is not greater than every expense number")
    return Store(expenses, _read_budgets(path, data["budgets"]), data["next_id"])


def load(path: str | Path) -> Store:
    """Read the file. A missing file is an empty store; a bad file raises and is left alone."""
    path = Path(path)
    if not path.exists():
        return Store.empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise _bad(path, "it cannot be read as JSON") from error
    return _parse(path, data)


def save(path: str | Path, store: Store) -> None:
    """Write the whole file to a temporary file in the same folder, then swap it in."""
    path = Path(path)
    data = {
        "version": 1,
        "next_id": store.next_id,
        "expenses": [
            {
                "id": e.id,
                "amount_paise": e.amount_paise,
                "category": e.category,
                "date": e.date,
                "description": e.description,
            }
            for e in store.expenses
        ],
        "budgets": dict(store.budgets),
    }
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    temporary = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            dir=path.parent, prefix=".expenses-", suffix=".tmp"
        )
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as error:
        if temporary is not None:
            with contextlib.suppress(OSError):
                os.unlink(temporary)
        message = f"{path.name} could not be saved: {error}"
        raise ExpenseError("storage-error", message, None) from error
