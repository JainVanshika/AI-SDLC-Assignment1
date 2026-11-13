"""Integrity gate: the tests, the harness, the specification and the project file are as they were
at the newest baseline tag. A recorded amendment adds a new tag; the old ones are never moved."""

import subprocess
from pathlib import Path

from common import Context, result, run

TAG_PATTERN = "baseline-1a-before-implement*"  # the first baseline and the amendments v2, v3, ...
PROTECTED = ["tests", ".harness", "specs/001-expense-tracker/spec.md", "pyproject.toml"]


def git_bytes(ctx: Context, *args: str) -> tuple[int, bytes]:
    done = subprocess.run(["git", *args], cwd=ctx.root, capture_output=True, check=False)  # noqa: S603, S607
    return done.returncode, done.stdout


def run_gate(ctx: Context) -> dict:
    top = run(["git", "rev-parse", "--show-toplevel"], ctx.root)["stdout"].strip()
    prefix = run(["git", "rev-parse", "--show-prefix"], ctx.root)["stdout"].strip()
    failures = []
    _, tags = git_bytes(ctx, "tag", "--list", TAG_PATTERN, "--sort=version:refname")
    names = [line for line in tags.decode().splitlines() if line]
    if not names:
        failures.append({"rule": "tag-missing", "message": f"no Git tag matches {TAG_PATTERN}"})
        summary = {
            "command": f"git tag --list {TAG_PATTERN}",
            "exit_status": 1,
            "stdout": "",
            "stderr": "",
        }
        return result("integrity", summary, failures)
    tag = names[-1]
    for path in PROTECTED:
        _, listing = git_bytes(ctx, "ls-tree", "-r", "--name-only", tag, "--", prefix + path)
        at_tag = {line for line in listing.decode().splitlines() if line}
        _, current = git_bytes(ctx, "ls-files", "-co", "--exclude-standard", "--", prefix + path)
        now = {line for line in current.decode().splitlines() if line}
        for name in sorted(at_tag):
            file = Path(top) / name
            _, original = git_bytes(ctx, "show", f"{tag}:{name}")
            if not file.exists():
                failures.append({"rule": "protected-file-deleted", "file": name})
            elif file.read_bytes() != original:
                failures.append({"rule": "protected-file-changed", "file": name})
        failures += [
            {"rule": "protected-file-added", "file": name} for name in sorted(now - at_tag)
        ]
    summary = {
        "command": f"compare {', '.join(PROTECTED)} with the tag {tag}",
        "exit_status": 1 if failures else 0,
        "stdout": f"{len(failures)} difference(s)",
        "stderr": "",
    }
    return result("integrity", summary, failures)
