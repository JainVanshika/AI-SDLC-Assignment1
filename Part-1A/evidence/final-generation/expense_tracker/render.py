"""Text and JSON output. Amounts are integer paise in JSON and rupees with two decimals in text."""

import json

from .models import BudgetWarning, Expense, Outcome
from .money import format_rupees

CATEGORY_WIDTH = 6  # the longest category, "travel"


def to_json(value: object) -> str:
    return json.dumps(value, sort_keys=True) + "\n"


def expense_dict(expense: Expense) -> dict[str, object]:
    return {
        "id": expense.id,
        "amount_paise": expense.amount_paise,
        "category": expense.category,
        "date": expense.date,
        "description": expense.description,
    }


def warning_dict(warning: BudgetWarning) -> dict[str, object]:
    return {
        "category": warning.category,
        "month": warning.month,
        "total_paise": warning.total_paise,
        "limit_paise": warning.limit_paise,
    }


def expense_line(expense: Expense) -> str:
    line = (
        f"#{expense.id}  {format_rupees(expense.amount_paise)}  "
        f"{expense.category:<{CATEGORY_WIDTH}}  {expense.date}"
    )
    return f"{line}  {expense.description}" if expense.description else line


def warning_line(warning: BudgetWarning) -> str:
    return (
        f"warning budget-exceeded: {warning.category} {warning.month} "
        f"total {format_rupees(warning.total_paise)} limit {format_rupees(warning.limit_paise)}"
    )


def saved(verb: str, outcome: Outcome, as_json: bool) -> str:
    """The result of an add or an edit, with any warnings."""
    if as_json:
        return to_json(
            {
                "expense": expense_dict(outcome.expense),
                "warnings": [warning_dict(w) for w in outcome.warnings],
            }
        )
    lines = [f"{verb} {expense_line(outcome.expense)}", *map(warning_line, outcome.warnings)]
    return "\n".join(lines) + "\n"


def listing(expenses: tuple[Expense, ...], as_json: bool) -> str:
    if as_json:
        return to_json({"expenses": [expense_dict(e) for e in expenses]})
    return "".join(expense_line(e) + "\n" for e in expenses)


def totals(month: str, values: dict[str, int], as_json: bool) -> str:
    if as_json:
        by_category = {k: v for k, v in values.items() if k != "overall"}
        return to_json({"month": month, "totals": by_category, "overall": values["overall"]})
    lines = [f"{k} {format_rupees(v)}" for k, v in values.items() if k != "overall"]
    return "\n".join([*lines, f"total {format_rupees(values['overall'])}"]) + "\n"


def status(month: str, rows: list[dict[str, int | str]], as_json: bool) -> str:
    if as_json:
        return to_json({"month": month, "budgets": rows})
    return "".join(
        f"{r['category']} limit {format_rupees(int(r['limit_paise']))} "
        f"spent {format_rupees(int(r['spent_paise']))} "
        f"remaining {format_rupees(int(r['remaining_paise']))}\n"
        for r in rows
    )
