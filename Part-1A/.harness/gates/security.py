"""Security gate: Bandit over the source; only medium and high findings count."""

import json
import sys

from common import Context, result, run


def run_gate(ctx: Context) -> dict:
    done = run([sys.executable, "-m", "bandit", "-r", "src", "-ll", "-f", "json", "-q"], ctx.root)
    failures = []
    try:
        report = json.loads(done["stdout"] or "{}")
        for issue in report.get("results", []):
            failures.append(
                {
                    "rule": issue["test_id"],
                    "file": issue["filename"].replace(str(ctx.root) + "/", ""),
                    "line": issue["line_number"],
                    "severity": issue["issue_severity"],
                    "message": issue["issue_text"],
                }
            )
    except json.JSONDecodeError:
        failures.append(
            {
                "rule": "bandit-output",
                "message": "Bandit did not print JSON",
                "detail": done["stderr"][-400:],
            }
        )
    if done["exit_status"] not in (0, 1) and not failures:
        failures.append(
            {
                "rule": "bandit-run",
                "message": f"Bandit exited with {done['exit_status']}",
                "detail": done["stderr"][-400:],
            }
        )
    return result("security", done, failures)
