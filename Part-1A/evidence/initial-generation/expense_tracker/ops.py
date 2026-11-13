"""The operations of the specification. Pure functions: each takes a Store and returns a new one."""

from dataclasses import replace

from . import money, rules
from .errors import ExpenseError
from .models import BudgetWarning, Expense, Outcome, Store


def _month_of(expense: Expense) -> str:
    return expense.date[:7]


def _total(store: Store, category: str, month: str) -> int:
    return sum(
        e.amount_paise for e in store.expenses if e.category == category and _month_of(e) == month
    )


def _warnings(store: Store, expense: Expense) -> tuple[BudgetWarning, ...]:
    limit = store.budgets.get(expense.category)
    if limit is None:
        return ()
    month = _month_of(expense)
    total = _total(store, expense.category, month)
    if total > limit:  # a total equal to the limit does not warn
        return (BudgetWarning(expense.category, month, total, limit),)
    return ()


def _find(store: Store, expense_id: object) -> Expense:
    wanted = rules.check_id(expense_id)
    for expense in store.expenses:
        if expense.id == wanted:
            return expense
    raise ExpenseError("not-found", f"there is no expense number {wanted}", "id")


def add_expense(
    store: Store, amount: object, category: object, date: object, description: str | None = ""
) -> Outcome:
    paise = money.parse_amount(amount)
    category = rules.check_category(category)
    date = rules.check_date(date)
    description = rules.check_description("" if description is None else description)
    expense = Expense(store.next_id, paise, category, date, description)
    new = replace(store, expenses=(*store.expenses, expense), next_id=store.next_id + 1)
    return Outcome(new, expense, _warnings(new, expense))


def edit_expense(
    store: Store,
    expense_id: object,
    amount: object = None,
    category: object = None,
    date: object = None,
    description: object = None,
) -> Outcome:
    current = _find(store, expense_id)
    if amount is None and category is None and date is None and description is None:
        raise ExpenseError("nothing-to-change", "give at least one value to change", None)
    changed = replace(
        current,
        amount_paise=current.amount_paise if amount is None else money.parse_amount(amount),
        category=current.category if category is None else rules.check_category(category),
        date=current.date if date is None else rules.check_date(date),
        description=current.description
        if description is None
        else rules.check_description(description),
    )
    expenses = tuple(changed if e.id == current.id else e for e in store.expenses)
    new = replace(store, expenses=expenses)
    return Outcome(new, changed, _warnings(new, changed))


def delete_expense(store: Store, expense_id: object) -> Store:
    current = _find(store, expense_id)
    return replace(store, expenses=tuple(e for e in store.expenses if e.id != current.id))


def list_expenses(
    store: Store, category: object = None, month: object = None
) -> tuple[Expense, ...]:
    wanted_category = None if category is None else rules.check_category(category)
    wanted_month = None if month is None else rules.check_month(month)
    chosen = [
        e
        for e in store.expenses
        if (wanted_category is None or e.category == wanted_category)
        and (wanted_month is None or _month_of(e) == wanted_month)
    ]
    return tuple(sorted(chosen, key=lambda e: (e.date, e.id)))


def monthly_totals(store: Store, month: object) -> dict[str, int]:
    wanted = rules.check_month(month)
    totals = dict.fromkeys(rules.CATEGORIES, 0)
    for expense in store.expenses:
        if _month_of(expense) == wanted:
            totals[expense.category] += expense.amount_paise
    totals["overall"] = sum(totals.values())
    return totals


def set_budget(store: Store, category: object, amount: object) -> Store:
    category = rules.check_category(category)
    limit = money.parse_amount(amount)
    return replace(store, budgets={**store.budgets, category: limit})


def remove_budget(store: Store, category: object) -> Store:
    category = rules.check_category(category)
    if category not in store.budgets:
        raise ExpenseError("not-found", f"no budget is set for {category}", "category")
    return replace(store, budgets={k: v for k, v in store.budgets.items() if k != category})


def budget_status(store: Store, month: object) -> list[dict[str, int | str]]:
    wanted = rules.check_month(month)
    status = []
    for category in rules.CATEGORIES:
        if category in store.budgets:
            limit = store.budgets[category]
            spent = _total(store, category, wanted)
            status.append(
                {
                    "category": category,
                    "limit_paise": limit,
                    "spent_paise": spent,
                    "remaining_paise": limit - spent,
                }
            )
    return status
