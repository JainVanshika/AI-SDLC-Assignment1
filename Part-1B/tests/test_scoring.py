import json

import pytest
import scoring
from conftest import ROOT
from layers import semantic

THRESHOLD = json.loads((ROOT / ".harness" / "threshold.json").read_text(encoding="utf-8"))
WEIGHTS = THRESHOLD["weights"]
LOG = {"decision": "log", "amount": "450.00", "category": "food", "date": "2026-11-13"}


def log_answer(**changes):
    expense = {"amount": "450.00", "category": "food", "date": "2026-11-13", "description": "lunch"}
    expense.update(changes)
    return {"model_calls": 1, "reply": {"decision": "log", "expense": expense}}


@pytest.mark.ac("AC-040")
@pytest.mark.parametrize(
    ("changes", "score"),
    [
        ({}, 1.0),
        ({"description": "any other words at all"}, 1.0),
        ({"amount": "451.00"}, 0.75),
        ({"category": "travel"}, 0.85),
        ({"date": "2026-11-12"}, 0.8),
        ({"amount": "451.00", "category": "travel", "date": "2026-11-12"}, 0.4),
    ],
)
def test_a_log_is_scored_by_amount_category_and_date_and_never_by_the_description(changes, score):
    case = {"expected": LOG}
    assert semantic.score(case, log_answer(**changes), WEIGHTS)["score"] == pytest.approx(score)


@pytest.mark.ac("AC-040")
def test_the_weights_of_every_decision_add_up_to_1():
    for weights in WEIGHTS.values():
        assert sum(weights.values()) == pytest.approx(1.0)


@pytest.mark.ac("AC-040")
def test_the_threshold_is_the_one_in_the_specification():
    assert THRESHOLD["overall_minimum"] == 0.85
    assert THRESHOLD["guardrail_case_minimum"] == 1.0
    assert THRESHOLD["layer1_required_rate"] == 1.0
    assert THRESHOLD["repetitions"] == 3


def values(**changes):
    base = {
        "overall_score": 0.95,
        "layer1_pass_rate": 1.0,
        "layer2_pass_rate": 1.0,
        "guardrail_pass_rate": 1.0,
        "stability": 1.0,
    }
    return {**base, **changes}


@pytest.mark.ac("AC-040")
@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({}, "PASS"),
        ({"overall_score": 0.85}, "PASS"),
        ({"overall_score": 0.849}, "FAIL"),
        ({"guardrail_pass_rate": 10 / 11}, "FAIL"),
        ({"layer1_pass_rate": 0.99}, "FAIL"),
        ({"stability": 0.5}, "PASS"),
    ],
)
def test_the_verdict_follows_the_pass_rule(changes, expected):
    assert scoring.verdict(values(**changes), THRESHOLD) == expected


@pytest.mark.ac("AC-040")
def test_a_failing_repetition_scores_zero_and_the_case_score_is_the_mean():
    case = {
        "id": "T",
        "guardrail": True,
        "text": "Paid 450 for lunch yesterday",
        "today": "2026-11-14",
        "expected": LOG,
    }
    broken = {
        "model_calls": 1,
        "reply": {
            "decision": "log",
            "expense": {
                "amount": "450",
                "category": "food",
                "date": "2026-11-13",
                "description": "x",
            },
        },
    }
    result = scoring.judge_case(
        case, [log_answer(), log_answer(), broken], WEIGHTS, ["FAKE-KEY-0123456789"]
    )
    assert result["score"] == pytest.approx(2 / 3, abs=1e-6)
    assert [bool(r["layer1"]) for r in result["repetitions"]] == [False, False, True]
    run = scoring.metrics([result])
    assert run["guardrail_pass_rate"] == 0.0
    assert run["layer1_pass_rate"] == pytest.approx(2 / 3)


@pytest.mark.ac("AC-040")
def test_stability_is_the_share_of_cases_with_the_same_decision_in_all_repetitions():
    case = {
        "id": "T",
        "guardrail": False,
        "text": "Paid 450 for lunch yesterday",
        "today": "2026-11-14",
        "expected": LOG,
    }
    refuse = {
        "model_calls": 1,
        "reply": {"decision": "refuse", "reason": "not-an-expense", "message": "no"},
    }
    steady = scoring.judge_case(case, [log_answer()] * 3, WEIGHTS, [])
    shaky = scoring.judge_case(case, [log_answer(), log_answer(), refuse], WEIGHTS, [])
    assert scoring.metrics([steady, shaky])["stability"] == 0.5
