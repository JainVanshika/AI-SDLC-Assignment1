"""Amounts: rupees as typed by a person, whole paise inside. Integer arithmetic only."""

import re

from .errors import ExpenseError

MAX_PAISE = 1_000_000_000  # INR 10,000,000.00
# [0-9] and not \d, because \d also matches the digits of other scripts
_AMOUNT = re.compile(r"(0|[1-9][0-9]*)(?:\.([0-9]{1,2}))?")
_MAX_WHOLE_DIGITS = 8  # 10,000,000 has eight digits


def _refuse() -> ExpenseError:
    return ExpenseError(
        "invalid-amount",
        "amount must be in rupees with up to two decimals, more than 0 and at most 10000000.00",
        "amount",
    )


def parse_amount(text: object) -> int:
    """Read rupees such as `450` or `450.50` and return whole paise (FR-002, FR-003)."""
    match = _AMOUNT.fullmatch(text) if isinstance(text, str) else None
    if match is None or len(match.group(1)) > _MAX_WHOLE_DIGITS:
        raise _refuse()
    whole, fraction = match.group(1), match.group(2) or ""
    paise = int(whole) * 100 + int(fraction.ljust(2, "0"))
    if not 1 <= paise <= MAX_PAISE:
        raise _refuse()
    return paise


def format_rupees(paise: int) -> str:
    """Show whole paise as rupees with two decimals, for example 12050 as `120.50`."""
    sign = "-" if paise < 0 else ""
    rupees, rest = divmod(abs(paise), 100)
    return f"{sign}{rupees}.{rest:02d}"
