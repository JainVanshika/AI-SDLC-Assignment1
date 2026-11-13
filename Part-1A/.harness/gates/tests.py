"""Tests gate: every test passes and branch coverage of the library is at least 90 per cent."""

import re
import sys
import xml.etree.ElementTree as ET  # noqa: S405 - reads the file pytest has just written

from common import Context, result, run


def run_gate(ctx: Context) -> dict:
    junit = ctx.out / "junit.xml"
    done = run(
        [
            sys.executable, "-m", "pytest", "tests",
            "--cov=src/expense_tracker", "--cov-branch", "--cov-fail-under=90", "--cov-report=term-missing",
            f"--junitxml={junit}", "-q", "-p", "no:cacheprovider",
        ],
        ctx.root,
    )  # fmt: skip
    failures = []
    if junit.exists():
        for case in ET.parse(junit).getroot().iter("testcase"):  # noqa: S314
            problem = (
                case.find("failure") if case.find("failure") is not None else case.find("error")
            )
            if problem is not None:
                failures.append(
                    {
                        "rule": "test-failed",
                        "test": f"{case.get('classname')}::{case.get('name')}",
                        "message": (problem.get("message") or "")[:300],
                    }
                )
    coverage = re.search(r"Total coverage: ([0-9.]+)%", done["stdout"])
    if "Coverage failure" in done["stdout"] or "FAIL Required test coverage" in done["stdout"]:
        failures.append(
            {
                "rule": "coverage",
                "expected": "at least 90%",
                "observed": f"{coverage.group(1)}%" if coverage else "see output",
            }
        )
    if done["exit_status"] != 0 and not failures:
        failures.append(
            {
                "rule": "pytest-run",
                "message": f"pytest exited with {done['exit_status']}",
                "detail": done["stdout"][-600:],
            }
        )
    return result("tests", done, failures)
