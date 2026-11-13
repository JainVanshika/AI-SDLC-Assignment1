import copy

import pytest
from conftest import GOOD_CLARIFY, GOOD_LOG, GOOD_REFUSE, TODAY

from expense_logger.contract import check_reply


@pytest.mark.ac("AC-034")
@pytest.mark.parametrize("reply", [GOOD_LOG, GOOD_CLARIFY, GOOD_REFUSE])
def test_a_good_reply_has_no_violation(reply):
    assert check_reply(reply, TODAY) == []


def broken(base, path, value):
    reply = copy.deepcopy(base)
    target = reply
    for key in path[:-1]:
        target = target[key]
    if value is KeyError:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return reply


BAD = {
    "not an object": ([1, 2], "INV-01"),
    "unknown decision": ({"decision": "save"}, "INV-01"),
    "log with extra field": (broken(GOOD_LOG, ["note"], "x"), "INV-02"),
    "log without expense": ({"decision": "log"}, "INV-02"),
    "expense with extra field": (broken(GOOD_LOG, ["expense", "id"], 1), "INV-02"),
    "expense without date": (broken(GOOD_LOG, ["expense", "date"], KeyError), "INV-02"),
    "amount as a number": (broken(GOOD_LOG, ["expense", "amount"], 450.0), "INV-03"),
    "amount with one decimal": (broken(GOOD_LOG, ["expense", "amount"], "450.5"), "INV-03"),
    "amount with a comma": (broken(GOOD_LOG, ["expense", "amount"], "1,200.00"), "INV-03"),
    "amount zero": (broken(GOOD_LOG, ["expense", "amount"], "0.00"), "INV-03"),
    "amount above the limit": (broken(GOOD_LOG, ["expense", "amount"], "10000000.01"), "INV-03"),
    "unknown category": (broken(GOOD_LOG, ["expense", "category"], "fun"), "INV-03"),
    "date not real": (broken(GOOD_LOG, ["expense", "date"], "2026-02-30"), "INV-04"),
    "date in another form": (broken(GOOD_LOG, ["expense", "date"], "13-11-2026"), "INV-04"),
    "description too long": (broken(GOOD_LOG, ["expense", "description"], "d" * 101), "INV-06"),
    "description empty": (broken(GOOD_LOG, ["expense", "description"], ""), "INV-06"),
    "clarify without missing": (broken(GOOD_CLARIFY, ["missing"], []), "INV-05"),
    "clarify with unknown item": (broken(GOOD_CLARIFY, ["missing"], ["colour"]), "INV-05"),
    "clarify with extra field": (broken(GOOD_CLARIFY, ["reason"], "x"), "INV-02"),
    "question empty": (broken(GOOD_CLARIFY, ["question"], ""), "INV-06"),
    "question too long": (broken(GOOD_CLARIFY, ["question"], "q" * 301), "INV-06"),
    "unknown reason": (broken(GOOD_REFUSE, ["reason"], "rude"), "INV-05"),
    "refuse without message": (broken(GOOD_REFUSE, ["message"], KeyError), "INV-02"),
    "message empty": (broken(GOOD_REFUSE, ["message"], ""), "INV-06"),
}


@pytest.mark.ac("AC-034")
@pytest.mark.parametrize("name", BAD)
def test_a_reply_that_breaks_the_contract_is_flagged_by_the_right_rule(name):
    reply, rule = BAD[name]
    assert any(v.startswith(rule) for v in check_reply(reply, TODAY)), check_reply(reply, TODAY)


@pytest.mark.ac("AC-008")
def test_a_description_of_100_characters_is_allowed():
    reply = broken(GOOD_LOG, ["expense", "description"], "d" * 100)
    assert check_reply(reply, TODAY) == []


@pytest.mark.ac("AC-020")
def test_a_clarify_reply_needs_a_question_and_allowed_missing_items():
    reply = {"decision": "clarify", "question": "Which currency?", "missing": ["currency", "date"]}
    assert check_reply(reply, TODAY) == []


@pytest.mark.ac("AC-024")
def test_a_refuse_reply_needs_an_allowed_reason_and_a_message():
    reply = {"decision": "refuse", "reason": "unsafe-request", "message": "I cannot do that."}
    assert check_reply(reply, TODAY) == []
