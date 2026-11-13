import http.client
import json

import pytest

from expense_logger import config
from expense_logger.model import GeminiClient, ModelUnavailable

KEY = "FAKE-KEY-0123456789"
REPLY = json.dumps({"candidates": [{"content": {"parts": [{"text": '{"decision": "refuse"}'}]}}]})


class FakeResponse:
    def __init__(self, status, body="", headers=None):
        self.status = status
        self._body = body.encode()
        self._headers = {k.lower(): v for k, v in (headers or {}).items()}

    def read(self):
        return self._body

    def getheader(self, name, default=None):
        return self._headers.get(name.lower(), default)


class Script:
    """A fake connection factory: each connection plays the next step (a response or an error)."""

    def __init__(self, *steps):
        self.steps = list(steps)
        self.requests = []
        self.timeouts = []

    def __call__(self, host, timeout=None):
        self.timeouts.append((host, timeout))
        return Connection(self)


class Connection:
    def __init__(self, script):
        self.script = script
        self.step = script.steps.pop(0)

    def request(self, method, path, body=None, headers=None):
        self.script.requests.append(
            {"method": method, "path": path, "body": body, "headers": headers}
        )

    def getresponse(self):
        if isinstance(self.step, Exception):
            raise self.step
        return self.step

    def close(self):
        pass


def client(script, waits):
    return GeminiClient(KEY, connection_factory=script, sleep=waits.append)


@pytest.mark.ac("AC-035")
def test_the_call_uses_temperature_0_json_output_and_the_key_only_in_the_header():
    script = Script(FakeResponse(200, REPLY))
    text = client(script, []).generate("the system prompt", "the user message")
    assert text == '{"decision": "refuse"}'
    sent = script.requests[0]
    assert sent["method"] == "POST"
    assert sent["path"] == f"/v1beta/models/{config.MODEL}:generateContent"
    assert sent["headers"]["x-goog-api-key"] == KEY
    body = json.loads(sent["body"])
    assert body["generationConfig"]["temperature"] == 0
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert body["systemInstruction"]["parts"][0]["text"] == "the system prompt"
    assert body["contents"][0]["parts"][0]["text"] == "the user message"
    assert KEY not in sent["path"] and KEY not in sent["body"]
    assert script.timeouts == [(config.API_HOST, 60)]


@pytest.mark.ac("AC-033")
def test_three_failures_then_a_success_waits_5_15_and_45_seconds():
    waits = []
    script = Script(
        FakeResponse(429), FakeResponse(500), FakeResponse(503), FakeResponse(200, REPLY)
    )
    assert client(script, waits).generate("s", "u") == '{"decision": "refuse"}'
    assert waits == [5, 15, 45]
    assert len(script.requests) == 4


@pytest.mark.ac("AC-033")
def test_when_every_try_fails_the_error_is_model_unavailable():
    waits = []
    script = Script(*[FakeResponse(503)] * 4)
    with pytest.raises(ModelUnavailable):
        client(script, waits).generate("s", "u")
    assert waits == [5, 15, 45]
    assert len(script.requests) == 4


@pytest.mark.ac("AC-033")
def test_a_retry_after_header_replaces_the_wait():
    waits = []
    script = Script(FakeResponse(429, headers={"Retry-After": "7"}), FakeResponse(200, REPLY))
    client(script, waits).generate("s", "u")
    assert waits == [7]


@pytest.mark.ac("AC-033")
@pytest.mark.parametrize(
    "error", [TimeoutError("slow"), http.client.RemoteDisconnected("gone"), OSError("down")]
)
def test_a_timeout_or_a_dropped_connection_is_retried(error):
    waits = []
    script = Script(error, FakeResponse(200, REPLY))
    assert client(script, waits).generate("s", "u")
    assert waits == [5]


@pytest.mark.ac("AC-033")
@pytest.mark.parametrize("status", [400, 401, 403, 404])
def test_other_failures_are_not_retried(status):
    waits = []
    script = Script(FakeResponse(status), FakeResponse(200, REPLY))
    with pytest.raises(ModelUnavailable):
        client(script, waits).generate("s", "u")
    assert waits == []
    assert len(script.requests) == 1


@pytest.mark.ac("AC-034")
def test_an_answer_without_text_gives_an_empty_string():
    script = Script(FakeResponse(200, json.dumps({"candidates": []})))
    assert client(script, []).generate("s", "u") == ""
