"""The command line: parse the arguments, call the library, print the result."""

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from . import ops, render, rules, storage
from .errors import ExpenseError
from .money import format_rupees

DEFAULT_FILE = "expenses.json"


def _common() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--file", default=DEFAULT_FILE, help="the data file")
    common.add_argument("--json", action="store_true", help="print JSON")
    return common


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="expense", description="A personal expense tracker.")
    sub = parser.add_subparsers(dest="command", required=True)
    common = _common()

    for name in ("add", "edit"):
        p = sub.add_parser(name, parents=[common])
        if name == "edit":
            p.add_argument("id")
        p.add_argument("--amount")
        p.add_argument("--category")
        p.add_argument("--date")
        p.add_argument("--description")
    p = sub.add_parser("list", parents=[common])
    p.add_argument("--category")
    p.add_argument("--month")
    p = sub.add_parser("delete", parents=[common])
    p.add_argument("id")
    p.add_argument("--yes", action="store_true", help="confirm the deletion")
    p = sub.add_parser("totals", parents=[common])
    p.add_argument("--month")
    budget = sub.add_parser("budget", help="monthly budgets").add_subparsers(
        dest="action", required=True
    )
    for name in ("set", "remove", "status"):
        p = budget.add_parser(name, parents=[common])
        if name == "status":
            p.add_argument("--month")
        else:
            p.add_argument("--category")
        if name == "set":
            p.add_argument("--amount")
    return parser


def _add(args: argparse.Namespace) -> str:
    path = Path(args.file)
    outcome = ops.add_expense(
        storage.load(path), args.amount, args.category, args.date, args.description
    )
    storage.save(path, outcome.store)
    return render.saved("added", outcome, args.json)


def _edit(args: argparse.Namespace) -> str:
    path = Path(args.file)
    outcome = ops.edit_expense(
        storage.load(path), args.id, args.amount, args.category, args.date, args.description
    )
    storage.save(path, outcome.store)
    return render.saved("edited", outcome, args.json)


def _delete(args: argparse.Namespace) -> str:
    if not args.yes:
        raise ExpenseError("confirmation-required", "add --yes to delete an expense", "yes")
    path = Path(args.file)
    expense_id = rules.check_id(args.id)
    storage.save(path, ops.delete_expense(storage.load(path), expense_id))
    return render.to_json({"deleted": expense_id}) if args.json else f"deleted #{expense_id}\n"


def _list(args: argparse.Namespace) -> str:
    found = ops.list_expenses(storage.load(Path(args.file)), args.category, args.month)
    return render.listing(found, args.json)


def _totals(args: argparse.Namespace) -> str:
    values = ops.monthly_totals(storage.load(Path(args.file)), args.month)
    return render.totals(args.month, values, args.json)


def _budget_set(args: argparse.Namespace) -> str:
    path = Path(args.file)
    store = ops.set_budget(storage.load(path), args.category, args.amount)
    storage.save(path, store)
    limit = store.budgets[args.category]
    if args.json:
        return render.to_json({"budget": {"category": args.category, "limit_paise": limit}})
    return f"budget {args.category} {format_rupees(limit)}\n"


def _budget_remove(args: argparse.Namespace) -> str:
    path = Path(args.file)
    storage.save(path, ops.remove_budget(storage.load(path), args.category))
    if args.json:
        return render.to_json({"removed": args.category})
    return f"removed budget {args.category}\n"


def _budget_status(args: argparse.Namespace) -> str:
    rows = ops.budget_status(storage.load(Path(args.file)), args.month)
    return render.status(args.month, rows, args.json)


HANDLERS: dict[tuple[str, str | None], Callable[[argparse.Namespace], str]] = {
    ("add", None): _add,
    ("edit", None): _edit,
    ("delete", None): _delete,
    ("list", None): _list,
    ("totals", None): _totals,
    ("budget", "set"): _budget_set,
    ("budget", "remove"): _budget_remove,
    ("budget", "status"): _budget_status,
}


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else 2
    try:
        output = HANDLERS[(args.command, getattr(args, "action", None))](args)
    except ExpenseError as error:
        print(f"error {error.code}: {error.message}", file=sys.stderr)
        return 3 if error.code == "storage-error" else 2
    sys.stdout.write(output)
    return 0
