import pytest

from expense_tracker.errors import ExpenseError
from expense_tracker.money import format_rupees, parse_amount

ACCEPTED = {
    "450": 45000,
    "450.5": 45050,
    "450.50": 45050,
    "0.50": 50,
    "0.01": 1,
    "10000000.00": 1_000_000_000,
}

REFUSED = [
    "10000000.01",
    "0",
    "0.00",
    "-5",
    "abc",
    "1e3",
    "450.505",
    ".5",
    "450.",
    "007",
    "4 50",
    "",
    " 450",
    "450 ",
    "1,000",
    "₹450",
    "+5",
    "٤٥٠",
    "٤٥٠.٥٠",
]


@pytest.mark.ac("AC-003")
@pytest.mark.parametrize(("text", "paise"), ACCEPTED.items())
def test_valid_amounts_become_whole_paise(text, paise):
    result = parse_amount(text)
    assert result == paise
    assert type(result) is int


@pytest.mark.ac("AC-004")
@pytest.mark.parametrize("text", REFUSED)
def test_invalid_amounts_are_refused(text):
    with pytest.raises(ExpenseError) as raised:
        parse_amount(text)
    assert raised.value.code == "invalid-amount"
    assert raised.value.field == "amount"


@pytest.mark.ac("AC-004")
@pytest.mark.parametrize("value", [None, 450, 450.5, True])
def test_an_amount_that_is_not_text_is_refused(value):
    with pytest.raises(ExpenseError) as raised:
        parse_amount(value)
    assert raised.value.code == "invalid-amount"


@pytest.mark.ac("AC-042")
@pytest.mark.parametrize(
    ("paise", "text"),
    [
        (12050, "120.50"),
        (45000, "450.00"),
        (50, "0.50"),
        (1, "0.01"),
        (0, "0.00"),
        (1_000_000_000, "10000000.00"),
    ],
)
def test_paise_are_shown_as_rupees_with_two_decimals(paise, text):
    assert format_rupees(paise) == text
