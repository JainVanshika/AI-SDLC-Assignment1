"""The checks that run before any model call, so that a broken build never uses model quota."""

import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET  # noqa: S405 - reads the file pytest has just written
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAG_PATTERN = "baseline-1b-before-implement*"
PROTECTED = ["tests", ".harness", "evals", "specs/001-expense-logger/spec.md", "pyproject.toml"]


def _run(cmd: list[str], cwd: Path = ROOT) -> dict:
    try:
        done = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=False, timeout=1800
        )  # noqa: S603
        return {
            "command": " ".join(cmd),
            "exit_status": done.returncode,
            "stdout": done.stdout,
            "stderr": done.stderr,
        }
    except FileNotFoundError as error:
        return {"command": " ".join(cmd), "exit_status": 127, "stdout": "", "stderr": str(error)}


def _gate(name: str, done: dict, failures: list[dict]) -> dict:
    return {
        "name": name,
        "status": "FAIL" if failures else "PASS",
        "command": done["command"],
        "exit_status": done["exit_status"],
        "failures": failures,
        "output_tail": (done["stdout"] + done["stderr"])[-1200:],
    }


def lint() -> dict:
    done = _run(
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
        ]
    )
    try:
        found = json.loads(done["stdout"] or "[]")
    except json.JSONDecodeError:
        found = [
            {
                "code": "ruff-output",
                "filename": "",
                "location": {"row": 0},
                "message": "Ruff did not print JSON",
            }
        ]
    failures = [
        {
            "rule": f["code"],
            "file": f["filename"].replace(str(ROOT) + "/", ""),
            "line": f["location"]["row"],
            "message": f["message"],
        }
        for f in found
    ]
    return _gate("lint", done, failures)


def security() -> dict:
    done = _run([sys.executable, "-m", "bandit", "-r", "src", "-ll", "-f", "json", "-q"])
    try:
        found = json.loads(done["stdout"] or "{}").get("results", [])
    except json.JSONDecodeError:
        found = [
            {
                "test_id": "bandit-output",
                "filename": "",
                "line_number": 0,
                "issue_text": "Bandit did not print JSON",
            }
        ]
    failures = [
        {
            "rule": f["test_id"],
            "file": f["filename"].replace(str(ROOT) + "/", ""),
            "line": f["line_number"],
            "message": f["issue_text"],
        }
        for f in found
    ]
    return _gate("security", done, failures)


def tests(out: Path) -> dict:
    junit = out / "junit.xml"
    done = _run(
        [
            sys.executable, "-m", "pytest", "tests", "--cov=src/expense_logger", "--cov-branch",
            "--cov-fail-under=90", f"--junitxml={junit}", "-q", "-p", "no:cacheprovider",
        ]
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
    if "Coverage failure" in done["stdout"] or "FAIL Required test coverage" in done["stdout"]:
        seen = re.search(r"Total coverage: ([0-9.]+)%", done["stdout"])
        failures.append(
            {
                "rule": "coverage",
                "expected": "at least 90%",
                "observed": f"{seen.group(1)}%" if seen else "see output",
            }
        )
    if done["exit_status"] != 0 and not failures:
        failures.append(
            {"rule": "pytest-run", "message": f"pytest exited with {done['exit_status']}"}
        )
    return _gate("tests", done, failures)


def secrets() -> dict:
    top = _run(["git", "rev-parse", "--show-toplevel"])["stdout"].strip()
    runs, failures = [], []
    with tempfile.TemporaryDirectory() as folder:
        jobs = [("history", ["gitleaks", "git", top])] + [
            (name, ["gitleaks", "dir", name])
            for name in [
                "src",
                "tests",
                ".harness",
                "specs",
                "evals",
                "evidence",
                "prompts",
                "pyproject.toml",
            ]
            if (ROOT / name).exists()
        ]
        for index, (label, command) in enumerate(jobs):
            report = Path(folder) / f"{index}.json"
            done = _run(command + ["--no-banner", "--redact", "-f", "json", "-r", str(report)])
            runs.append(done)
            if done["exit_status"] == 127:
                failures.append(
                    {"rule": "gitleaks-missing", "message": "gitleaks is not installed"}
                )
                break
            for leak in json.loads(report.read_text() or "[]") if report.exists() else []:
                failures.append(
                    {
                        "rule": leak["RuleID"],
                        "scope": label,
                        "file": leak["File"],
                        "line": leak["StartLine"],
                    }
                )
    return _gate(
        "secrets",
        {
            "command": " && ".join(r["command"] for r in runs),
            "exit_status": 1 if failures else 0,
            "stdout": "",
            "stderr": "",
        },
        failures,
    )


def traceability() -> dict:
    spec = (ROOT / "specs/001-expense-logger/spec.md").read_text(encoding="utf-8")
    defined = set(re.findall(r"^\| (AC-\d{3}) \|", spec, re.M))
    cited: set[str] = set()
    for path in (ROOT / "tests").rglob("test_*.py"):
        for marker in re.findall(r"mark\.ac\(([^)]*)\)", path.read_text(encoding="utf-8")):
            cited.update(re.findall(r"AC-\d{3}", marker))
    for case in json.loads((ROOT / "evals/dataset.json").read_text(encoding="utf-8")):
        cited.update(case["covers"])
    failures = [{"rule": "ac-without-test-or-case", "ac": ac} for ac in sorted(defined - cited)]
    failures += [{"rule": "cites-unknown-ac", "ac": ac} for ac in sorted(cited - defined)]
    done = {
        "command": "read the spec, tests/ and evals/dataset.json",
        "exit_status": 1 if failures else 0,
        "stdout": f"{len(defined)} criteria, {len(defined & cited)} cited",
        "stderr": "",
    }
    return _gate("traceability", done, failures)


def integrity() -> dict:
    def git(*args: str) -> bytes:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False).stdout  # noqa: S603, S607

    top = Path(git("rev-parse", "--show-toplevel").decode().strip())
    prefix = git("rev-parse", "--show-prefix").decode().strip()
    names = [
        n
        for n in git("tag", "--list", TAG_PATTERN, "--sort=version:refname").decode().splitlines()
        if n
    ]
    if not names:
        done = {
            "command": f"git tag --list {TAG_PATTERN}",
            "exit_status": 1,
            "stdout": "",
            "stderr": "",
        }
        return _gate(
            "integrity",
            done,
            [{"rule": "tag-missing", "message": f"no Git tag matches {TAG_PATTERN}"}],
        )
    tag, failures = names[-1], []
    for path in PROTECTED:
        at_tag = {
            n
            for n in git("ls-tree", "-r", "--name-only", tag, "--", prefix + path)
            .decode()
            .splitlines()
            if n
        }
        now = {
            n
            for n in git("ls-files", "-co", "--exclude-standard", "--", prefix + path)
            .decode()
            .splitlines()
            if n
        }
        for name in sorted(at_tag):
            file = top / name
            if not file.exists():
                failures.append({"rule": "protected-file-deleted", "file": name})
            elif file.read_bytes() != git("show", f"{tag}:{name}"):
                failures.append({"rule": "protected-file-changed", "file": name})
        failures += [{"rule": "protected-file-added", "file": n} for n in sorted(now - at_tag)]
    done = {
        "command": f"compare {', '.join(PROTECTED)} with the tag {tag}",
        "exit_status": 1 if failures else 0,
        "stdout": "",
        "stderr": "",
    }
    return _gate("integrity", done, failures)


def run_all(out: Path) -> list[dict]:
    return [lint(), security(), tests(out), secrets(), traceability(), integrity()]
