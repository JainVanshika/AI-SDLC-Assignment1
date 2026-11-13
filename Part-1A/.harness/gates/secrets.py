"""Secrets gate: gitleaks over the whole Git history and over the files of the project, no allowlist."""

import json
import tempfile
from pathlib import Path

from common import Context, result, run

FILES = ["src", "tests", ".harness", "specs", "evidence", "pyproject.toml"]


def scan(command: list[str], report: Path, ctx: Context):
    done = run(command + ["--no-banner", "--redact", "-f", "json", "-r", str(report)], ctx.root)
    leaks = json.loads(report.read_text() or "[]") if report.exists() else []
    return done, leaks


def run_gate(ctx: Context) -> dict:
    top = run(["git", "rev-parse", "--show-toplevel"], ctx.root)["stdout"].strip()
    runs, failures = [], []
    with tempfile.TemporaryDirectory() as folder:
        jobs = [("history", ["gitleaks", "git", top])]
        jobs += [(name, ["gitleaks", "dir", name]) for name in FILES if (ctx.root / name).exists()]
        for index, (label, command) in enumerate(jobs):
            done, leaks = scan(command, Path(folder) / f"{index}.json", ctx)
            runs.append(done)
            if done["exit_status"] == 127:
                failures.append(
                    {"rule": "gitleaks-missing", "message": "gitleaks is not installed"}
                )
                break
            if done["exit_status"] not in (0, 1):
                failures.append(
                    {"rule": "gitleaks-run", "scope": label, "message": done["stderr"][-300:]}
                )
            for leak in leaks:
                failures.append(
                    {
                        "rule": leak["RuleID"],
                        "scope": label,
                        "file": leak["File"],
                        "line": leak["StartLine"],
                    }
                )
    return result("secrets", runs, failures)
