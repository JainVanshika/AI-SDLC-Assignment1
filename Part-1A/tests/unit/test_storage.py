import json

import pytest
from expense_tracker.errors import ExpenseError
from expense_tracker.models import Store
from helpers import reference_store

from expense_tracker import ops, storage

GOOD = {
    "version": 1,
    "next_id": 2,
    "expenses": [
        {
            "id": 1,
            "amount_paise": 45000,
            "category": "food",
            "date": "2026-11-10",
            "description": "lunch",
        }
    ],
    "budgets": {"food": 60000},
}


def write(path, data):
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def mutated(**changes):
    data = json.loads(json.dumps(GOOD))
    data.update(changes)
    return data


@pytest.mark.ac("AC-036")
def test_what_is_saved_loads_back_exactly(tmp_path):
    path = tmp_path / "e.json"
    store = ops.set_budget(reference_store(), "food", "600.00")
    storage.save(path, store)
    loaded = storage.load(path)
    assert loaded.expenses == store.expenses
    assert dict(loaded.budgets) == dict(store.budgets)
    assert loaded.next_id == store.next_id


@pytest.mark.ac("AC-037")
def test_a_missing_file_is_an_empty_store_and_the_first_save_creates_it(tmp_path):
    path = tmp_path / "new.json"
    empty = storage.load(path)
    assert (empty.expenses, dict(empty.budgets), empty.next_id) == ((), {}, 1)
    assert not path.exists()
    storage.save(path, ops.add_expense(empty, "1.00", "other", "2026-11-01").store)
    assert path.exists()


@pytest.mark.ac("AC-038")
def test_a_file_that_is_not_json_is_refused_and_left_alone(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("this is not json", encoding="utf-8")
    with pytest.raises(ExpenseError) as raised:
        storage.load(path)
    assert raised.value.code == "storage-error"
    assert path.read_text(encoding="utf-8") == "this is not json"


BAD_FILES = {
    "float amount": mutated(expenses=[{**GOOD["expenses"][0], "amount_paise": 450.5}]),
    "boolean amount": mutated(expenses=[{**GOOD["expenses"][0], "amount_paise": True}]),
    "zero amount": mutated(expenses=[{**GOOD["expenses"][0], "amount_paise": 0}]),
    "unknown category": mutated(expenses=[{**GOOD["expenses"][0], "category": "x"}]),
    "bad date": mutated(expenses=[{**GOOD["expenses"][0], "date": "2026-02-30"}]),
    "long description": mutated(expenses=[{**GOOD["expenses"][0], "description": "d" * 101}]),
    "repeated id": mutated(expenses=[GOOD["expenses"][0], GOOD["expenses"][0]], next_id=3),
    "next_id too small": mutated(next_id=1),
    "extra field": mutated(extra=1),
    "extra expense field": mutated(expenses=[{**GOOD["expenses"][0], "note": "x"}]),
    "missing field": {k: v for k, v in GOOD.items() if k != "budgets"},
    "other version": mutated(version=2),
    "float budget": mutated(budgets={"food": 600.5}),
    "unknown budget category": mutated(budgets={"x": 100}),
    "not an object": [1, 2, 3],
}


@pytest.mark.ac("AC-039")
@pytest.mark.parametrize("name", BAD_FILES)
def test_a_file_with_wrong_content_is_refused_and_left_alone(tmp_path, name):
    path = write(tmp_path / "bad.json", BAD_FILES[name])
    before = path.read_bytes()
    with pytest.raises(ExpenseError) as raised:
        storage.load(path)
    assert raised.value.code == "storage-error"
    assert path.read_bytes() == before


@pytest.mark.ac("AC-039")
def test_a_good_file_loads(tmp_path):
    store = storage.load(write(tmp_path / "good.json", GOOD))
    assert store.next_id == 2
    assert store.budgets["food"] == 60000
    assert store.expenses[0].amount_paise == 45000


@pytest.mark.ac("AC-040")
def test_a_failed_write_leaves_the_old_file_and_no_leftovers(tmp_path, monkeypatch):
    path = tmp_path / "e.json"
    storage.save(path, reference_store())
    before = path.read_bytes()

    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("expense_tracker.storage.os.replace", boom)
    with pytest.raises(ExpenseError) as raised:
        storage.save(path, Store.empty())
    assert raised.value.code == "storage-error"
    assert path.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["e.json"]
    monkeypatch.undo()
    assert len(storage.load(path).expenses) == 4
