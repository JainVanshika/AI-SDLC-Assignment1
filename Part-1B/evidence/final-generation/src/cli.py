"""The command line: read the arguments, call the assistant, print one line of JSON."""

import argparse
import hashlib
import json
import os
from collections.abc import Sequence
from pathlib import Path

from . import assistant, config
from .model import GeminiClient

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "system.md"


def _info(prompt: bytes) -> dict:
    return {
        "model": config.MODEL,
        "temperature": config.TEMPERATURE,
        "response_mime_type": config.RESPONSE_MIME_TYPE,
        "timeout_seconds": config.TIMEOUT_SECONDS,
        "max_retries": config.MAX_RETRIES,
        "max_text_length": config.MAX_TEXT_LENGTH,
        "prompt_sha256": hashlib.sha256(prompt).hexdigest(),
    }


def _emit(answer: dict) -> int:
    print(json.dumps(answer, sort_keys=True, ensure_ascii=False))
    return 2 if "error" in answer else 0


def main(argv: Sequence[str] | None = None, client: assistant.Client | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="expense-logger", description="Log an expense from a sentence."
    )
    parser.add_argument("text", nargs="?", default="", help="the request text")
    parser.add_argument(
        "--today", help="the reference date, YYYY-MM-DD (never read from the clock)"
    )
    parser.add_argument(
        "--info", action="store_true", help="print the model, settings and prompt hash"
    )
    args = parser.parse_args(argv)
    prompt = PROMPT_PATH.read_bytes()
    if args.info:
        print(json.dumps(_info(prompt)))
        return 0
    problem = assistant.validate_request(args.text, args.today)
    if problem:
        return _emit(problem)
    if client is None:
        key = os.environ.get("GEMINI_API_KEY", "")
        if not key:
            return _emit(
                assistant.error("missing-api-key", "set the environment variable GEMINI_API_KEY")
            )
        client = GeminiClient(key)
    return _emit(assistant.handle(args.text, args.today, client, prompt.decode("utf-8")))
