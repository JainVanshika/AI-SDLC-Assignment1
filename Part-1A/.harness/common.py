"""Shared helpers for the gates: run a command and keep what it printed."""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Context:
    root: Path
    out: Path  # folder of this run


def run(cmd: list[str], cwd: Path = ROOT, timeout: int = 1800) -> dict:
    """Run a command; never raise. Returns the command, exit status, output and duration."""
    started = time.monotonic()
    text = " ".join(str(part) for part in cmd)
    try:
        done = subprocess.run(  # noqa: S603 - the commands are fixed lists written in the gates
            [str(part) for part in cmd],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        status, stdout, stderr = done.returncode, done.stdout, done.stderr
    except FileNotFoundError as error:
        status, stdout, stderr = 127, "", f"command not found: {error}"
    except subprocess.TimeoutExpired:
        status, stdout, stderr = 124, "", f"timed out after {timeout} seconds"
    return {
        "command": text,
        "exit_status": status,
        "stdout": stdout,
        "stderr": stderr,
        "seconds": round(time.monotonic() - started, 2),
    }


def result(name: str, executed: dict | list[dict], failures: list[dict]) -> dict:
    """A gate result: PASS only when there is no failure."""
    runs = executed if isinstance(executed, list) else [executed]
    return {
        "name": name,
        "status": "FAIL" if failures else "PASS",
        "command": " && ".join(r["command"] for r in runs),
        "exit_status": next((r["exit_status"] for r in runs if r["exit_status"] != 0), 0),
        "stdout": "\n".join(r["stdout"] for r in runs),
        "stderr": "\n".join(r["stderr"] for r in runs),
        "failures": failures,
    }
