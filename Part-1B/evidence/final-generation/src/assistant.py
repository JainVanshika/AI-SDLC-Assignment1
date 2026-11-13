"""One request, from text to answer."""

import json
import re
from datetime import date
from typing import Protocol

from . import config
from .contract import check_reply
from .model import ModelUnavailable


class Client(Protocol):
    def generate(self, system: str, user: str) -> str: ...


def error(code: str, message: str, model_calls: int = 0) -> dict:
    return {"model_calls": model_calls, "error": {"code": code, "message": message}}


def _real_date(value: object) -> bool:
    if not (isinstance(value, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value)):
        return False
    try:
        date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        return False
    return True


def validate_request(text: object, today: object) -> dict | None:
    """The checks that need no model: the reference date, then the text. None means all is well."""
    if not _real_date(today):
        return error("invalid-reference-date", "the reference date must be a real date, YYYY-MM-DD")
    if not isinstance(text, str) or not text.strip():
        return error("empty-request", "the request is empty")
    if len(text) > config.MAX_TEXT_LENGTH:
        return error(
            "request-too-long", f"the request is longer than {config.MAX_TEXT_LENGTH} characters"
        )
    return None


def handle(text: str, today: str, client: Client, system_prompt: str) -> dict:
    """Return the answer for one request: {model_calls, reply} or {model_calls, error}."""
    problem = validate_request(text, today)
    if problem:
        return problem
    user = f"Reference date: {today}\n<request>\n{text}\n</request>"
    try:
        raw = client.generate(system_prompt, user)
    except ModelUnavailable as failure:
        return error("model-unavailable", str(failure), 1)
    try:
        reply = json.loads(raw)
    except ValueError:
        return error("reply-not-json", "the model's reply is not JSON", 1)
    violations = check_reply(reply, today)
    if violations:
        return error(
            "invalid-reply", "the reply breaks the contract: " + "; ".join(violations[:3]), 1
        )
    return {"model_calls": 1, "reply": reply}
