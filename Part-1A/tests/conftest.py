"""Shared test helpers: the ac marker, in-process and subprocess command line runners."""

import subprocess
import sys
from pathlib import Path

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "ac(id): acceptance criterion the test checks")


@pytest.fixture
def run(capsys: pytest.CaptureFixture[str]):
    """Run the command line in this process; return (status, standard output, standard error)."""

    def _run(*args: str) -> tuple[int, str, str]:
        from expense_tracker import cli

        capsys.readouterr()
        status = cli.main(list(args))
        captured = capsys.readouterr()
        return status, captured.out, captured.err

    return _run


def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Start the command line as a separate process, as a user would."""
    return subprocess.run(
        [sys.executable, "-m", "expense_tracker", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
