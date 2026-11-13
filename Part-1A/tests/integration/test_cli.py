import json

import pytest
from conftest import run_cli

from expense_tracker import ops
from expense_tracker.models import Store

ADD_1 = [
    "add",
    "--amount",
    "450.00",
    "--category",
    "food",
    "--date",
    "2026-11-10",
    "--description",
    "lunch",
]
ADD_2 = ["add", "--amount", "120.50", "--category", "food", "--date", "2026-11-12"]
ADD_3 = [
    "add",
    "--amount",
    "300.00",
    "--category",
    "travel",
    "--date",
    "2026-11-15",
    "--description",
    "bus",
]


@pytest.fixture
def file(tmp_path):
    return str(tmp_path / "e.json")


def seed(run, file):
    for args in (ADD_1, ADD_2, ADD_3):
        assert run(*args, "--file", file)[0] == 0


@pytest.mark.ac("AC-041")
def test_every_operation_is_available_on_the_command_line(run, file):
    seed(run, file)
    assert run("list", "--file", file)[0] == 0
    assert run("edit", "1", "--amount", "460.00", "--file", file)[0] == 0
    assert run("totals", "--month", "2026-11", "--file", file)[0] == 0
    assert run("budget", "set", "--category", "food", "--amount", "600.00", "--file", file)[0] == 0
    assert run("budget", "status", "--month", "2026-11", "--file", file)[0] == 0
    assert run("budget", "remove", "--category", "food", "--file", file)[0] == 0
    assert run("delete", "3", "--yes", "--file", file)[0] == 0


@pytest.mark.ac("AC-042")
def test_text_output_shows_rupees_with_two_decimals(run, file):
    status, out, _ = run(*ADD_1, "--file", file)
    assert status == 0
    assert out.split() == ["added", "#1", "450.00", "food", "2026-11-10", "lunch"]
    run(*ADD_2, "--file", file)
    _, out, _ = run("list", "--file", file)
    lines = [line.split() for line in out.splitlines()]
    assert lines == [
        ["#1", "450.00", "food", "2026-11-10", "lunch"],
        ["#2", "120.50", "food", "2026-11-12"],
    ]


@pytest.mark.ac("AC-042")
def test_text_totals(run, file):
    seed(run, file)
    _, out, _ = run("totals", "--month", "2026-11", "--file", file)
    assert [line.split() for line in out.splitlines()] == [
        ["food", "570.50"],
        ["travel", "300.00"],
        ["bills", "0.00"],
        ["other", "0.00"],
        ["total", "870.50"],
    ]


@pytest.mark.ac("AC-042")
def test_json_output_has_integers_in_paise_and_equals_the_library(run, file):
    status, out, _ = run(*ADD_1, "--json", "--file", file)
    assert status == 0
    assert out.count("\n") == 1
    data = json.loads(out)
    expected = ops.add_expense(Store.empty(), "450.00", "food", "2026-11-10", "lunch").expense
    assert data == {
        "expense": {
            "id": expected.id,
            "amount_paise": expected.amount_paise,
            "category": expected.category,
            "date": expected.date,
            "description": expected.description,
        },
        "warnings": [],
    }
    assert type(data["expense"]["amount_paise"]) is int


@pytest.mark.ac("AC-042")
def test_json_totals_and_status(run, file):
    seed(run, file)
    run("budget", "set", "--category", "food", "--amount", "600.00", "--file", file)
    _, out, _ = run("totals", "--month", "2026-11", "--json", "--file", file)
    assert json.loads(out) == {
        "month": "2026-11",
        "totals": {"food": 57050, "travel": 30000, "bills": 0, "other": 0},
        "overall": 87050,
    }
    _, out, _ = run("budget", "status", "--month", "2026-11", "--json", "--file", file)
    assert json.loads(out) == {
        "month": "2026-11",
        "budgets": [
            {
                "category": "food",
                "limit_paise": 60000,
                "spent_paise": 57050,
                "remaining_paise": 2950,
            }
        ],
    }


@pytest.mark.ac("AC-043")
def test_a_warning_still_exits_with_0_and_is_shown(run, file):
    run("budget", "set", "--category", "food", "--amount", "10.00", "--file", file)
    status, out, err = run(
        "add", "--amount", "20.00", "--category", "food", "--date", "2026-11-01", "--file", file
    )
    assert status == 0
    assert "warning budget-exceeded" in out
    assert err == ""
    status, out, _ = run(
        "add",
        "--amount",
        "20.00",
        "--category",
        "food",
        "--date",
        "2026-11-02",
        "--json",
        "--file",
        file,
    )
    assert json.loads(out)["warnings"] == [
        {"category": "food", "month": "2026-11", "total_paise": 4000, "limit_paise": 1000}
    ]


@pytest.mark.ac("AC-043")
@pytest.mark.parametrize(
    ("args", "code"),
    [
        (
            ["add", "--amount", "450.505", "--category", "food", "--date", "2026-11-10"],
            "invalid-amount",
        ),
        (["add", "--amount", "5", "--category", "x", "--date", "2026-11-10"], "invalid-category"),
        (["list", "--month", "2026-13"], "invalid-month"),
        (["delete", "abc", "--yes"], "invalid-id"),
        (["delete", "99", "--yes"], "not-found"),
        (["edit", "1"], "nothing-to-change"),
    ],
)
def test_invalid_input_exits_with_2_and_writes_only_to_standard_error(run, file, args, code):
    run(*ADD_1, "--file", file)
    status, out, err = run(*args, "--file", file)
    assert status == 2
    assert out == ""
    assert err.startswith(f"error {code}: ")


@pytest.mark.ac("AC-043")
def test_a_bad_data_file_exits_with_3(run, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    status, out, err = run("list", "--file", str(bad))
    assert (status, out) == (3, "")
    assert err.startswith("error storage-error: ")
    assert bad.read_text(encoding="utf-8") == "not json"


@pytest.mark.ac("AC-044")
@pytest.mark.parametrize(
    ("args", "code"),
    [
        (["add", "--amount", "1.00", "--category", "food"], "invalid-date"),
        (["add", "--category", "food", "--date", "2026-11-10"], "invalid-amount"),
        (["add", "--amount", "1.00", "--date", "2026-11-10"], "invalid-category"),
    ],
)
def test_a_missing_value_is_refused_with_the_code_of_that_field(run, file, args, code):
    status, out, err = run(*args, "--file", file)
    assert (status, out) == (2, "")
    assert err.startswith(f"error {code}: ")


@pytest.mark.ac("AC-044")
def test_the_same_command_twice_gives_the_same_output(run, file):
    seed(run, file)
    first = run("list", "--month", "2026-11", "--json", "--file", file)
    second = run("list", "--month", "2026-11", "--json", "--file", file)
    assert first == second


@pytest.mark.ac("AC-046")
def test_delete_without_yes_is_refused_and_deletes_nothing(run, file):
    seed(run, file)
    status, out, err = run("delete", "2", "--file", file)
    assert (status, out) == (2, "")
    assert err.startswith("error confirmation-required: ")
    _, listing, _ = run("list", "--json", "--file", file)
    assert [e["id"] for e in json.loads(listing)["expenses"]] == [1, 2, 3]


@pytest.mark.ac("AC-034")
def test_delete_with_yes_removes_the_expense(run, file):
    seed(run, file)
    status, out, _ = run("delete", "2", "--yes", "--json", "--file", file)
    assert status == 0
    assert json.loads(out) == {"deleted": 2}
    _, listing, _ = run("list", "--json", "--file", file)
    assert [e["id"] for e in json.loads(listing)["expenses"]] == [1, 3]


@pytest.mark.ac("AC-047")
def test_the_default_file_is_expenses_json_in_the_current_folder(run, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert run(*ADD_1)[0] == 0
    assert (tmp_path / "expenses.json").exists()


@pytest.mark.ac("AC-047")
def test_a_given_path_is_used_and_no_other_file_is_created(run, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    other = tmp_path / "other.json"
    assert run(*ADD_1, "--file", str(other))[0] == 0
    assert other.exists()
    assert not (tmp_path / "expenses.json").exists()


@pytest.mark.ac("AC-041")
def test_the_program_also_runs_as_a_separate_process(tmp_path):
    result = run_cli(["list", "--json", "--file", str(tmp_path / "e.json")], tmp_path)
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"expenses": []}
    failed = run_cli(["delete", "1", "--yes", "--file", str(tmp_path / "e.json")], tmp_path)
    assert failed.returncode == 2
    assert failed.stdout == ""
    assert failed.stderr.startswith("error not-found: ")
