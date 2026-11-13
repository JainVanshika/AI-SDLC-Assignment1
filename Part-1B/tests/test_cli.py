import hashlib
import json
from pathlib import Path

import pytest
from conftest import GOOD_CLARIFY, GOOD_LOG, GOOD_REFUSE, ROOT, TODAY

from expense_logger import cli, config
from expense_logger.model import GeminiClient, ModelUnavailable

KEY = "FAKE-KEY-0123456789"


def run(capsys, argv, **kwargs):
    capsys.readouterr()
    status = cli.main(argv, **kwargs)
    captured = capsys.readouterr()
    return status, captured.out, captured.err


@pytest.mark.ac("AC-036")
def test_info_prints_the_model_the_settings_and_the_prompt_hash_without_a_key(
    capsys, monkeypatch, fake
):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = fake("")
    status, out, _ = run(capsys, ["--info"], client=client)
    info = json.loads(out)
    prompt = (ROOT / "prompts" / "system.md").read_bytes()
    assert status == 0
    assert info == {
        "model": config.MODEL,
        "temperature": 0,
        "response_mime_type": "application/json",
        "timeout_seconds": 60,
        "max_retries": 3,
        "max_text_length": 1000,
        "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
    }
    assert client.calls == []


@pytest.mark.ac("AC-044")
@pytest.mark.parametrize("reply", [GOOD_LOG, GOOD_CLARIFY, GOOD_REFUSE])
def test_an_answer_is_one_line_of_json_and_exits_0(capsys, fake, reply):
    status, out, err = run(
        capsys, ["Paid 450 for lunch yesterday", "--today", TODAY], client=fake(json.dumps(reply))
    )
    assert status == 0
    assert out.count("\n") == 1
    assert json.loads(out) == {"model_calls": 1, "reply": reply}
    assert err == ""


@pytest.mark.ac("AC-044")
@pytest.mark.parametrize(
    ("argv", "code"),
    [
        ([""], "invalid-reference-date"),
        (["", "--today", TODAY], "empty-request"),
        (["x" * 1001, "--today", TODAY], "request-too-long"),
        (["Paid 450", "--today", "2026-13-01"], "invalid-reference-date"),
        (["Paid 450"], "invalid-reference-date"),
    ],
)
def test_an_error_is_one_line_of_json_and_exits_2(capsys, fake, argv, code):
    status, out, _ = run(capsys, argv, client=fake(json.dumps(GOOD_LOG)))
    assert status == 2
    assert out.count("\n") == 1
    answer = json.loads(out)
    assert (answer["error"]["code"], answer["model_calls"]) == (code, 0)


@pytest.mark.ac("AC-044")
def test_a_reply_that_breaks_the_contract_exits_2(capsys, fake):
    status, out, _ = run(capsys, ["Paid 450", "--today", TODAY], client=fake('{"decision": "log"}'))
    assert status == 2
    assert json.loads(out)["error"]["code"] == "invalid-reply"


@pytest.mark.ac("AC-037")
def test_a_missing_key_gives_missing_api_key_and_no_model_call(capsys, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    status, out, _ = run(capsys, ["Paid 450 for lunch", "--today", TODAY])
    assert status == 2
    answer = json.loads(out)
    assert (answer["error"]["code"], answer["model_calls"]) == ("missing-api-key", 0)


@pytest.mark.ac("AC-027")
def test_the_key_is_never_printed_even_when_the_service_fails(capsys, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", KEY)

    def failing(host, timeout=None):
        raise OSError(f"cannot reach {host}")

    broken = GeminiClient(KEY, connection_factory=failing, sleep=lambda seconds: None)
    status, out, err = run(capsys, ["Paid 450 for lunch", "--today", TODAY], client=broken)
    assert status == 2
    assert json.loads(out)["error"]["code"] == "model-unavailable"
    assert KEY not in out + err


@pytest.mark.ac("AC-027")
def test_the_key_is_not_in_the_source_files():
    for path in [*Path(ROOT / "src").rglob("*.py"), ROOT / "prompts" / "system.md"]:
        assert KEY not in path.read_text(encoding="utf-8")
        assert "GEMINI_API_KEY=" not in path.read_text(encoding="utf-8")


@pytest.mark.ac("AC-033")
def test_a_service_failure_exits_2_with_model_unavailable(capsys, fake):
    status, out, _ = run(
        capsys, ["Paid 450", "--today", TODAY], client=fake(error=ModelUnavailable("down"))
    )
    assert status == 2
    assert json.loads(out)["error"]["code"] == "model-unavailable"
