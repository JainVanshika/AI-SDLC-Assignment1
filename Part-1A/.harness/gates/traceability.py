"""Traceability gate: every acceptance criterion of the specification is cited by a test, and no test cites an unknown one."""

import re

from common import Context, result

SPEC = "specs/001-expense-tracker/spec.md"


def run_gate(ctx: Context) -> dict:
    spec = (ctx.root / SPEC).read_text(encoding="utf-8")
    defined = set(re.findall(r"^\| (AC-\d{3}) \|", spec, re.M))
    cited: dict[str, set[str]] = {}
    for path in sorted((ctx.root / "tests").rglob("test_*.py")):
        for marker in re.findall(r"mark\.ac\(([^)]*)\)", path.read_text(encoding="utf-8")):
            for ac in re.findall(r"AC-\d{3}", marker):
                cited.setdefault(ac, set()).add(path.name)
    failures = [{"rule": "ac-without-test", "ac": ac} for ac in sorted(defined - cited.keys())]
    failures += [
        {"rule": "test-cites-unknown-ac", "ac": ac, "files": sorted(cited[ac])}
        for ac in sorted(cited.keys() - defined)
    ]
    summary = {
        "command": f"read {SPEC} and tests/**/test_*.py",
        "exit_status": 1 if failures else 0,
        "stdout": f"{len(defined)} acceptance criteria, {len(defined & cited.keys())} cited by tests",
        "stderr": "",
    }
    return result("traceability", summary, failures)
