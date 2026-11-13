import ast
import random
import time
from pathlib import Path

from expense_tracker.models import Expense, Store

from expense_tracker import ops

SRC = Path(__file__).resolve().parents[2] / "src" / "expense_tracker"
FORBIDDEN_IMPORTS = {"time", "random", "socket", "urllib", "http", "requests", "secrets"}
FORBIDDEN_CALLS = {"today", "now", "utcnow", "time", "monotonic", "perf_counter"}


def source_trees():
    return [
        (path, ast.parse(path.read_text(encoding="utf-8"))) for path in sorted(SRC.glob("*.py"))
    ]


def test_the_source_never_reads_the_clock_random_numbers_or_the_network():
    """FR-022."""
    for path, tree in source_trees():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                names = {(node.module or "").split(".")[0]}
            else:
                names = set()
            assert not names & FORBIDDEN_IMPORTS, f"{path.name} imports {names & FORBIDDEN_IMPORTS}"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                assert node.func.attr not in FORBIDDEN_CALLS, f"{path.name} calls {node.func.attr}"


def test_the_source_never_uses_a_float():
    """Constitution principle I: no floating-point numbers for money."""
    for path, tree in source_trees():
        for node in ast.walk(tree):
            assert not (isinstance(node, ast.Constant) and isinstance(node.value, float)), path.name
            assert not (isinstance(node, ast.Name) and node.id == "float"), path.name
            if path.name not in {"storage.py", "cli.py"}:  # these two join paths with "/"
                assert not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)), (
                    f"{path.name} uses true division"
                )


def test_stored_amounts_are_always_plain_integers():
    rng = random.Random(7)
    store = Store.empty()
    for _ in range(200):
        text = f"{rng.randint(0, 999)}.{rng.randint(0, 99):02d}"
        if text in {"0.00"}:
            continue
        store = ops.add_expense(
            store, text, rng.choice(["food", "travel", "bills", "other"]), "2026-11-01"
        ).store
    assert all(type(e.amount_paise) is int for e in store.expenses)


def test_the_same_input_gives_the_same_output():
    def build():
        store = Store.empty()
        store = ops.set_budget(store, "food", "100.00")
        for i in range(30):
            store = ops.add_expense(store, f"{i + 1}.25", "food", f"2026-11-{i % 28 + 1:02d}").store
        return (
            ops.list_expenses(store),
            ops.monthly_totals(store, "2026-11"),
            ops.budget_status(store, "2026-11"),
        )

    assert build() == build()


def test_ten_thousand_expenses_list_and_total_in_under_two_seconds():
    """SC-003."""
    expenses = tuple(
        Expense(
            i,
            100 + i,
            ["food", "travel", "bills", "other"][i % 4],
            f"2026-{i % 12 + 1:02d}-{i % 28 + 1:02d}",
            "",
        )
        for i in range(1, 10_001)
    )
    store = Store(expenses, {}, 10_001)
    started = time.perf_counter()
    assert len(ops.list_expenses(store)) == 10_000
    assert ops.monthly_totals(store, "2026-05")["overall"] > 0
    assert time.perf_counter() - started < 2.0
