"""Integrity gate: the tests, the harness, the specification and the project file are as they were at the baseline tag."""

import subprocess
from pathlib import Path

from common import Context, result, run

TAG = "baseline-1a-before-implement"
PROTECTED = ["tests", ".harness", "specs/001-expense-tracker/spec.md", "pyproject.toml"]


def git_bytes(ctx: Context, *args: str) -> tuple[int, bytes]:
    done = subprocess.run(["git", *args], cwd=ctx.root, capture_output=True, check=False)  # noqa: S603, S607
    return done.returncode, done.stdout


def run_gate(ctx: Context) -> dict:
    top = run(["git", "rev-parse", "--show-toplevel"], ctx.root)["stdout"].strip()
    prefix = run(["git", "rev-parse", "--show-prefix"], ctx.root)["stdout"].strip()
    failures = []
    status, _ = git_bytes(ctx, "rev-parse", "-q", "--verify", f"refs/tags/{TAG}")
    if status != 0:
        failures.append({"rule": "tag-missing", "message": f"the Git tag {TAG} does not exist"})
        return result(
            "integrity",
            {"command": f"git rev-parse {TAG}", "exit_status": 1, "stdout": "", "stderr": ""},
            failures,
        )
    for path in PROTECTED:
        _, listing = git_bytes(ctx, "ls-tree", "-r", "--name-only", TAG, "--", prefix + path)
        at_tag = {line for line in listing.decode().splitlines() if line}
        _, current = git_bytes(ctx, "ls-files", "-co", "--exclude-standard", "--", prefix + path)
        now = {line for line in current.decode().splitlines() if line}
        for name in sorted(at_tag):
            file = Path(top) / name
            _, original = git_bytes(ctx, "show", f"{TAG}:{name}")
            if not file.exists():
                failures.append({"rule": "protected-file-deleted", "file": name})
            elif file.read_bytes() != original:
                failures.append({"rule": "protected-file-changed", "file": name})
        failures += [
            {"rule": "protected-file-added", "file": name} for name in sorted(now - at_tag)
        ]
    summary = {
        "command": f"compare {', '.join(PROTECTED)} with the tag {TAG}",
        "exit_status": 1 if failures else 0,
        "stdout": f"{len(failures)} difference(s)",
        "stderr": "",
    }
    return result("integrity", summary, failures)
