"""Load and validate the evaluation dataset."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = {"log", "clarify", "refuse", "error"}
CASE_KEYS = {"id", "category", "text", "today", "expected", "guardrail", "covers"}
LOG_KEYS = {"decision", "amount", "category", "date"}
FORBIDDEN = [
    re.compile(r"[^\s@]+@[^\s@]+\.[a-z]{2,}", re.I),
    re.compile(r"(?<![0-9.])[0-9]{10,}(?![0-9])"),
]


def load(path: Path | None = None) -> list[dict]:
    """Read the dataset and refuse a malformed one."""
    path = path or ROOT / "evals" / "dataset.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    seen = set()
    for case in cases:
        if set(case) != CASE_KEYS:
            raise ValueError(f"{case.get('id')}: fields are {sorted(case)}")
        if case["id"] in seen:
            raise ValueError(f"{case['id']} is used twice")
        seen.add(case["id"])
        expected = case["expected"]
        if expected.get("decision") not in DECISIONS:
            raise ValueError(f"{case['id']}: unknown decision")
        if expected["decision"] == "log" and set(expected) != LOG_KEYS:
            raise ValueError(f"{case['id']}: a log case needs {sorted(LOG_KEYS)}")
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", case["today"]):
            raise ValueError(f"{case['id']}: bad reference date")
        if not case["covers"]:
            raise ValueError(f"{case['id']}: covers no criterion")
    return cases


def looks_real(text: str) -> bool:
    """True when a request contains an email address or a long number such as a phone number."""
    return any(pattern.search(text) for pattern in FORBIDDEN)
