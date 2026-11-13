"""An independent check: totals and budget warnings recomputed with SQLite integer sums."""

import random
import sqlite3

import pytest

from expense_tracker import ops
from expense_tracker.models import Store

CATEGORIES = ["food", "travel", "bills", "other"]


def rupees(paise: int) -> str:
    return f"{paise // 100}.{paise % 100:02d}"


def random_run(seed: int):
    rng = random.Random(seed)
    store = Store.empty()
    for category in CATEGORIES:
        if rng.random() < 0.6:
            store = ops.set_budget(store, category, rupees(rng.randint(100, 500_000)))
    database = sqlite3.connect(":memory:")
    database.execute("create table e (amount integer, category text, month text)")
    checks = []
    for _ in range(rng.randint(1, 12)):
        paise = rng.randint(1, 300_000)
        category = rng.choice(CATEGORIES)
        month = f"2026-{rng.randint(1, 12):02d}"
        outcome = ops.add_expense(
            store, rupees(paise), category, f"{month}-{rng.randint(1, 28):02d}"
        )
        store = outcome.store
        database.execute("insert into e values (?, ?, ?)", (paise, category, month))
        total = database.execute(
            "select sum(amount) from e where category = ? and month = ?", (category, month)
        ).fetchone()[0]
        checks.append((outcome, category, month, total))
    return store, database, checks


@pytest.mark.parametrize("seed", range(1000))
def test_totals_and_warnings_match_an_independent_integer_computation(seed):
    store, database, checks = random_run(seed)
    for outcome, category, _month, total in checks:
        limit = store.budgets.get(category)
        expected_warning = limit is not None and total > limit
        # the budget never changes during the run, so the final limit is the limit at every step
        assert bool(outcome.warnings) == expected_warning
        if expected_warning:
            warning = outcome.warnings[0]
            assert (warning.total_paise, warning.limit_paise) == (total, limit)
    for month in {f"2026-{m:02d}" for m in range(1, 13)}:
        totals = ops.monthly_totals(store, month)
        rows = dict(
            database.execute(
                "select category, sum(amount) from e where month = ? group by category", (month,)
            )
        )
        for category in CATEGORIES:
            assert totals[category] == rows.get(category, 0)
        assert totals["overall"] == sum(rows.values())
