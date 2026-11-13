"""Lint gate: Ruff over the source and the tests, with its cache switched off."""

import json
import sys

from common import Context, result, run


def run_gate(ctx: Context) -> dict:
    done = run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "src",
            "tests",
            "--no-cache",
            "--output-format",
            "json",
        ],
        ctx.root,
    )
    failures = []
    try:
        for finding in json.loads(done["stdout"] or "[]"):
            failures.append(
                {
                    "rule": finding["code"],
                    "file": finding["filename"].replace(str(ctx.root) + "/", ""),
                    "line": finding["location"]["row"],
                    "message": finding["message"],
                }
            )
    except json.JSONDecodeError:
        failures.append(
            {
                "rule": "ruff-output",
                "message": "Ruff did not print JSON",
                "detail": done["stderr"][-400:],
            }
        )
    if done["exit_status"] not in (0, 1) and not failures:
        failures.append(
            {
                "rule": "ruff-run",
                "message": f"Ruff exited with {done['exit_status']}",
                "detail": done["stderr"][-400:],
            }
        )
    return result("lint", done, failures)
