"""The call to Google Gemini, with the retry rule of the specification (FR-013, FR-016)."""

import http.client
import json
import time
from collections.abc import Callable

from . import config


class ModelUnavailable(Exception):
    """The model service could not give an answer."""


class GeminiClient:
    """Sends one request and returns the text of the model's answer.

    The connection factory and the sleep function are parameters so that tests can replace them.
    """

    def __init__(
        self,
        api_key: str,
        connection_factory: Callable[
            ..., http.client.HTTPSConnection
        ] = http.client.HTTPSConnection,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._key = api_key
        self._connect = connection_factory
        self._sleep = sleep

    def _body(self, system: str, user: str) -> str:
        return json.dumps(
            {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {
                    "temperature": config.TEMPERATURE,
                    "responseMimeType": config.RESPONSE_MIME_TYPE,
                },
            }
        )

    def _once(self, body: str) -> tuple[int, str, str | None]:
        """One try: status, body and Retry-After header. May raise OSError or HTTPException."""
        connection = self._connect(config.API_HOST, timeout=config.TIMEOUT_SECONDS)
        try:
            connection.request(
                "POST",
                f"/v1beta/models/{config.MODEL}:generateContent",
                body,
                {"content-type": "application/json", "x-goog-api-key": self._key},
            )
            response = connection.getresponse()
            return (
                response.status,
                response.read().decode("utf-8", "replace"),
                response.getheader("Retry-After"),
            )
        finally:
            connection.close()

    @staticmethod
    def _text(body: str) -> str:
        try:
            return str(json.loads(body)["candidates"][0]["content"]["parts"][0]["text"])
        except (KeyError, IndexError, TypeError, ValueError):
            return ""

    def generate(self, system: str, user: str) -> str:
        body = self._body(system, user)
        wait: float | None = None
        for attempt in range(config.MAX_RETRIES + 1):
            if attempt:
                self._sleep(wait if wait is not None else config.RETRY_WAITS[attempt - 1])
            wait = None
            try:
                status, text, retry_after = self._once(body)
            except (OSError, http.client.HTTPException):
                continue
            if status == 200:
                return self._text(text)
            if status != 429 and status < 500:
                raise ModelUnavailable(f"the service answered with status {status}")
            if retry_after and retry_after.isdigit():
                wait = int(retry_after)
        raise ModelUnavailable("the service did not answer after the retries")
