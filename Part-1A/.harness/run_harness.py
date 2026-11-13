"""The harness runner. It runs the gates as separate processes and never imports the application.

uv run python .harness/run_harness.py [--run-id NAME] [--out FOLDER] [--gates lint,tests]
"""

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from common import ROOT, Context  # noqa: E402
from gates import integrity, lint, secrets, security, tests, traceability  # noqa: E402

GATES = {
    "lint": lint,
    "security": security,
    "secrets": secrets,
    "tests": tests,
    "traceability": traceability,
    "integrity": integrity,
}


def next_run_id(base: Path) -> str:
    taken = [
        int(p.name.split("-")[1]) for p in base.glob("run-*") if p.name.split("-")[1].isdigit()
    ]
    return f"run-{max(taken, default=0) + 1}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    parser.add_argument("--out", default=str(ROOT / "evidence" / "harness-results"))
    parser.add_argument("--gates", default=",".join(GATES))
    args = parser.parse_args()

    base = Path(args.out)
    run_id = args.run_id or next_run_id(base)
    folder = base / run_id
    folder.mkdir(parents=True, exist_ok=False)
    ctx = Context(root=ROOT, out=folder)
    started = time.monotonic()

    gates, failed = [], []
    for name in args.gates.split(","):
        outcome = GATES[name].run_gate(ctx)
        (folder / f"{name}.stdout.txt").write_text(outcome["stdout"], encoding="utf-8")
        (folder / f"{name}.stderr.txt").write_text(outcome["stderr"], encoding="utf-8")
        (folder / f"{name}.result.json").write_text(
            json.dumps(
                {k: v for k, v in outcome.items() if k not in ("stdout", "stderr")}, indent=2
            )
            + "\n",
            encoding="utf-8",
        )
        gates.append({"name": name, "status": outcome["status"]})
        print(f"{outcome['status']} {name}")
        if outcome["status"] == "FAIL":
            failed.append(
                {
                    "gate": name,
                    "command": outcome["command"],
                    "exit_status": outcome["exit_status"],
                    "failures": outcome["failures"],
                    "output_tail": (outcome["stdout"] + outcome["stderr"])[-1500:],
                }
            )
    verdict = "FAIL" if failed else "PASS"
    (folder / "summary.txt").write_text(
        "\n".join(f"{g['status']} {g['name']}" for g in gates) + f"\n{verdict}\n", encoding="utf-8"
    )
    (folder / "results.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "verdict": verdict,
                "gates": gates,
                "duration_seconds": round(time.monotonic() - started, 1),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if failed:
        (folder / "feedback.json").write_text(
            json.dumps({"failed_gates": failed}, indent=2) + "\n", encoding="utf-8"
        )
    print(verdict)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
