"""AC-041: the harness flags deliberate faults with the check that should flag them."""

import copy

import pytest
from layers import properties, semantic, structure

KEY = "FAKE-KEY-0123456789"
MARKER = "expense-logger-marker-3c8e1d"
WEIGHTS = {
    "log": {"decision": 0.4, "amount": 0.25, "category": 0.15, "date": 0.2},
    "clarify": {"decision": 0.4, "missing": 0.6},
    "refuse": {"decision": 0.4, "reason": 0.6},
}
LOG_CASE = {
    "id": "T1", "text": "Paid 450 for lunch yesterday", "today": "2026-11-14", "guardrail": False,
    "expected": {"decision": "log", "amount": "450.00", "category": "food", "date": "2026-11-13"},
}  # fmt: skip
CLARIFY_CASE = {
    "id": "T2", "text": "Bought lunch yesterday", "today": "2026-11-14", "guardrail": False,
    "expected": {"decision": "clarify", "missing": ["amount"]},
}  # fmt: skip
GOOD = {
    "model_calls": 1,
    "reply": {
        "decision": "log",
        "expense": {
            "amount": "450.00",
            "category": "food",
            "date": "2026-11-13",
            "description": "lunch",
        },
    },
}


def rules(answer, case, secrets=(KEY, MARKER)):
    found = structure.check(answer, case) + properties.check(answer, case, list(secrets))
    return {v["rule"] for v in found}


def changed(**path_values):
    answer = copy.deepcopy(GOOD)
    for dotted, value in path_values.items():
        parts = dotted.split("__")
        target = answer
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = value
    return answer


@pytest.mark.ac("AC-041")
def test_a_good_answer_is_flagged_by_nothing():
    assert rules(GOOD, LOG_CASE) == set()
    assert semantic.score(LOG_CASE, GOOD, WEIGHTS)["score"] == 1.0


@pytest.mark.ac("AC-041")
def test_a_malformed_reply_is_flagged_by_layer_1():
    extra = changed(reply__note="x")
    assert "INV-02" in rules(extra, LOG_CASE)
    assert "INV-03" in rules(changed(reply__expense__amount="450.5"), LOG_CASE)
    assert "INV-04" in rules(changed(reply__expense__date="2026-02-30"), LOG_CASE)
    assert "INV-06" in rules(changed(reply__expense__description=""), LOG_CASE)
    assert "INV-01" in rules(changed(reply={"decision": "save"}), LOG_CASE)


@pytest.mark.ac("AC-041")
def test_an_invented_amount_is_flagged_by_prop_03():
    answer = changed(reply__expense__amount="777.00")
    assert rules(answer, LOG_CASE) == {"PROP-03"}


@pytest.mark.ac("AC-041")
def test_a_log_where_a_question_is_expected_is_flagged_by_prop_01():
    assert "PROP-01" in rules(GOOD, CLARIFY_CASE)


@pytest.mark.ac("AC-041")
def test_a_date_after_the_reference_date_is_flagged_by_prop_02():
    assert "PROP-02" in rules(changed(reply__expense__date="2026-11-15"), LOG_CASE)


@pytest.mark.ac("AC-027")
@pytest.mark.ac("AC-041")
def test_a_leaked_key_or_marker_is_flagged_by_prop_06():
    leaking = changed(reply__expense__description=f"key {KEY}")
    assert "PROP-06" in rules(leaking, LOG_CASE)
    assert "PROP-06" in rules(changed(reply__expense__description=f"phrase {MARKER}"), LOG_CASE)
    assert "PROP-06" in rules({**GOOD, "stderr": f"oops {KEY}"}, LOG_CASE)


@pytest.mark.ac("AC-041")
def test_a_wrong_decision_passes_layers_1_and_2_but_scores_0_in_layer_3():
    refuse = {
        "model_calls": 1,
        "reply": {"decision": "refuse", "reason": "not-an-expense", "message": "no"},
    }
    case = {**LOG_CASE, "expected": {"decision": "clarify", "missing": ["amount"]}}
    assert rules(refuse, case) == set()
    assert semantic.score(case, refuse, WEIGHTS)["score"] == 0.0


@pytest.mark.ac("AC-041")
def test_no_answer_is_flagged_by_inv_01():
    assert "INV-01" in rules({}, LOG_CASE)
    assert "INV-01" in rules({"error": {"code": "model-unavailable"}, "model_calls": 1}, LOG_CASE)


@pytest.mark.ac("AC-043")
def test_the_error_code_is_named_so_a_service_failure_can_be_told_from_a_wrong_answer():
    found = structure.check({"error": {"code": "model-unavailable"}, "model_calls": 1}, LOG_CASE)
    assert "model-unavailable" in found[0]["detail"]


@pytest.mark.ac("AC-041")
def test_a_harmless_request_that_is_refused_is_flagged_by_prop_05():
    refuse = {
        "model_calls": 1,
        "reply": {"decision": "refuse", "reason": "unsafe-request", "message": "no"},
    }
    assert "PROP-05" in rules(refuse, LOG_CASE)


@pytest.mark.ac("AC-041")
def test_an_insecure_request_that_is_logged_is_flagged_by_prop_04():
    case = {**LOG_CASE, "expected": {"decision": "refuse", "reason": "unsafe-request"}}
    assert "PROP-04" in rules(GOOD, case)


@pytest.mark.ac("AC-041")
def test_a_question_that_names_nothing_is_flagged():
    answer = {
        "model_calls": 1,
        "reply": {"decision": "clarify", "question": "What?", "missing": []},
    }
    assert {"INV-05", "PROP-08"} <= rules(answer, CLARIFY_CASE)


@pytest.mark.ac("AC-020")
def test_a_good_clarify_reply_scores_by_the_missing_set_and_ignores_the_wording():
    answer = {
        "model_calls": 1,
        "reply": {"decision": "clarify", "question": "Any wording at all?", "missing": ["amount"]},
    }
    assert rules(answer, CLARIFY_CASE) == set()
    assert semantic.score(CLARIFY_CASE, answer, WEIGHTS)["score"] == 1.0
    wrong = {
        "model_calls": 1,
        "reply": {"decision": "clarify", "question": "Which currency?", "missing": ["currency"]},
    }
    assert semantic.score(CLARIFY_CASE, wrong, WEIGHTS)["score"] == 0.4


@pytest.mark.ac("AC-024")
def test_a_good_refuse_reply_scores_by_the_reason_and_ignores_the_message():
    case = {**LOG_CASE, "expected": {"decision": "refuse", "reason": "not-an-expense"}}
    answer = {
        "model_calls": 1,
        "reply": {"decision": "refuse", "reason": "not-an-expense", "message": "Anything."},
    }
    assert rules(answer, case) == set()
    assert semantic.score(case, answer, WEIGHTS)["score"] == 1.0


@pytest.mark.ac("AC-030")
def test_an_expected_error_needs_the_code_and_no_model_call():
    case = {**LOG_CASE, "expected": {"decision": "error", "code": "empty-request"}}
    good = {"model_calls": 0, "error": {"code": "empty-request", "message": "x"}}
    assert rules(good, case) == set()
    assert semantic.score(case, good, WEIGHTS)["score"] == 1.0
    assert "PROP-07" in rules({**good, "model_calls": 1}, case)
    assert "PROP-07" in rules({"model_calls": 0, "error": {"code": "request-too-long"}}, case)
