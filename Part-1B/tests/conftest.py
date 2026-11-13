"""Shared test helpers: the ac marker, a fake model client, and the harness on the import path."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".harness"))  # the harness modules are tested directly

TODAY = "2026-11-14"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "ac(id): acceptance criterion the test checks")


class FakeClient:
    """Stands in for the model service: returns a prepared text, or raises a prepared error."""

    def __init__(self, text: str = "", error: Exception | None = None) -> None:
        self.text = text
        self.error = error
        self.calls: list[tuple[str, str]] = []

    def generate(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if self.error is not None:
            raise self.error
        return self.text


@pytest.fixture
def fake():
    return FakeClient


GOOD_LOG = {
    "decision": "log",
    "expense": {
        "amount": "450.00",
        "category": "food",
        "date": "2026-11-13",
        "description": "lunch",
    },
}
GOOD_CLARIFY = {"decision": "clarify", "question": "How much did you pay?", "missing": ["amount"]}
GOOD_REFUSE = {"decision": "refuse", "reason": "not-an-expense", "message": "I only log expenses."}
