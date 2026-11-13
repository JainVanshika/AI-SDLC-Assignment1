import re
from collections import Counter

import dataset
import pytest
from conftest import ROOT

SPEC = (ROOT / "specs" / "001-expense-logger" / "spec.md").read_text(encoding="utf-8")
KNOWN = set(re.findall(r"^\| (AC-\d{3}) \|", SPEC, re.M))


@pytest.fixture(scope="module")
def cases():
    return dataset.load()


@pytest.mark.ac("AC-039")
def test_the_dataset_has_at_least_32_cases_with_unique_ids(cases):
    assert len(cases) >= 32
    assert len({c["id"] for c in cases}) == len(cases)


@pytest.mark.ac("AC-039")
def test_every_case_cites_criteria_that_exist(cases):
    for case in cases:
        assert set(case["covers"]) <= KNOWN, case["id"]


@pytest.mark.ac("AC-039")
def test_the_dataset_has_every_kind_of_ground_truth_and_at_least_8_guardrail_cases(cases):
    kinds = Counter(c["expected"]["decision"] for c in cases)
    assert set(kinds) == {"log", "clarify", "refuse", "error"}
    assert sum(c["guardrail"] for c in cases) >= 8


@pytest.mark.ac("AC-039")
def test_every_missing_item_and_every_reason_and_category_appears_in_the_ground_truth(cases):
    missing = {
        m for c in cases if c["expected"]["decision"] == "clarify" for m in c["expected"]["missing"]
    }
    reasons = {c["expected"]["reason"] for c in cases if c["expected"]["decision"] == "refuse"}
    categories = {c["expected"]["category"] for c in cases if c["expected"]["decision"] == "log"}
    assert missing == {"amount", "currency", "date", "single-expense"}
    assert reasons == {"not-an-expense", "unsafe-request"}
    assert categories == {"food", "travel", "bills", "other"}


@pytest.mark.ac("AC-039")
def test_the_ground_truth_dates_follow_the_reference_date_rule(cases):
    by_text = {c["text"]: c["expected"] for c in cases}
    assert by_text["Paid 450 for lunch yesterday"]["date"] == "2026-11-13"
    assert by_text["Coffee 120 the day before yesterday"]["date"] == "2026-11-12"
    assert by_text["Metro card recharge 300 on Monday"]["date"] == "2026-11-09"
    assert by_text["Petrol 2000 on Friday"]["date"] == "2026-11-13"
    assert all(c["today"] == "2026-11-14" for c in cases)


@pytest.mark.ac("AC-045")
def test_no_case_looks_like_real_data(cases):
    for case in cases:
        assert not dataset.looks_real(case["text"]), case["id"]


@pytest.mark.ac("AC-045")
def test_the_check_for_real_looking_data_works():
    assert dataset.looks_real("mail me at someone@example.com")
    assert dataset.looks_real("call 9876543210 now")
    assert not dataset.looks_real("Paid 10000000 for a car today")
    assert not dataset.looks_real("Spent 10000001 on a house deposit today")
