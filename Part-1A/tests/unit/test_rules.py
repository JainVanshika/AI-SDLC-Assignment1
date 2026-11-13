import pytest
from expense_tracker.errors import ExpenseError

from expense_tracker import rules


def code_of(check, value):
    with pytest.raises(ExpenseError) as raised:
        check(value)
    return raised.value.code, raised.value.field


@pytest.mark.ac("AC-005")
@pytest.mark.parametrize("category", ["food", "travel", "bills", "other"])
def test_the_four_categories_are_accepted(category):
    assert rules.check_category(category) == category


@pytest.mark.ac("AC-005")
@pytest.mark.parametrize("category", ["entertainment", "Food", "FOOD", "", " food", "food ", None])
def test_other_categories_are_refused(category):
    assert code_of(rules.check_category, category) == ("invalid-category", "category")


@pytest.mark.ac("AC-006")
@pytest.mark.parametrize("date", ["2026-11-10", "2028-02-29", "2099-12-31", "1900-01-01"])
def test_real_calendar_dates_are_accepted(date):
    assert rules.check_date(date) == date


@pytest.mark.ac("AC-006")
@pytest.mark.parametrize(
    "date",
    [
        "2026-02-30",
        "2026-13-01",
        "10-11-2026",
        "2026-1-5",
        "",
        "2027-02-29",
        "20261110",
        "2026-W45-2",
        "2026-11-10 ",
        "0000-01-01",
        "٢٠٢٦-١١-١٠",
        None,
    ],
)
def test_invalid_dates_are_refused(date):
    assert code_of(rules.check_date, date) == ("invalid-date", "date")


@pytest.mark.ac("AC-007")
def test_description_of_100_characters_is_accepted_and_101_is_refused():
    assert rules.check_description("x" * 100) == "x" * 100
    assert code_of(rules.check_description, "x" * 101) == ("invalid-description", "description")


@pytest.mark.ac("AC-007")
def test_an_empty_description_is_accepted():
    assert rules.check_description("") == ""


@pytest.mark.ac("AC-016")
@pytest.mark.ac("AC-020")
@pytest.mark.parametrize("month", ["2026-11", "2026-01", "2026-12"])
def test_valid_months_are_accepted(month):
    assert rules.check_month(month) == month


@pytest.mark.ac("AC-016")
@pytest.mark.ac("AC-020")
@pytest.mark.parametrize(
    "month", ["2026-13", "2026-1", "Nov", "2026-00", "", "2026-11-10", "26-11", " 2026-11", None]
)
def test_invalid_months_are_refused(month):
    assert code_of(rules.check_month, month) == ("invalid-month", "month")


@pytest.mark.ac("AC-033")
@pytest.mark.parametrize("value", ["1", "17", 1, 99])
def test_valid_ids_are_accepted(value):
    assert rules.check_id(value) == int(value)


@pytest.mark.ac("AC-033")
@pytest.mark.parametrize("value", ["abc", "0", "-1", "1.5", "", " 1", 0, -1, 1.5, True, None, "٣"])
def test_invalid_ids_are_refused(value):
    assert code_of(rules.check_id, value) == ("invalid-id", "id")
