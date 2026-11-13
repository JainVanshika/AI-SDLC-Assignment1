"""The evaluation runner. It runs the application as a separate process and never imports it.

uv run --env-file .env python .harness/run_eval.py [--run-id NAME] [--out FOLDER] [--cases C01,C02]
"""

import argparse
import json
import os
import shlex
import subprocess  # noqa: S404 - the application is started as a separate process on purpose
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import dataset  # noqa: E402
import prechecks  # noqa: E402
import scoring  # noqa: E402

ROOT = prechecks.ROOT
DEFAULT_APP = [sys.executable, "-m", "expense_logger"]


def load_key() -> str:
    """The key from the environment or from the ignored .env file. It is never printed or saved."""
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def run_app(app: list[str], case: dict, key: str, timeout: int) -> dict:
    """Run the application once on one case and return what it printed, parsed."""
    env = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}
    if key:
        env["GEMINI_API_KEY"] = key
    try:
        done = subprocess.run(  # noqa: S603
            [*app, case["text"], "--today", case["today"]],
            capture_output=True, text=True, timeout=timeout, env=env, cwd=ROOT, check=False,
        )  # fmt: skip
        out, err, status = done.stdout, done.stderr, done.returncode
    except subprocess.TimeoutExpired:
        out, err, status = "", "timed out", 124
    lines = [line for line in out.splitlines() if line.strip()]
    answer: dict = {}
    if lines:
        try:
            parsed = json.loads(lines[-1])
            answer = parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            answer = {}
    answer.update({"exit_status": status, "stdout": out, "stderr": err})
    return answer


def app_info(app: list[str]) -> dict:
    done = subprocess.run([*app, "--info"], capture_output=True, text=True, cwd=ROOT, check=False)  # noqa: S603
    try:
        return json.loads(done.stdout)
    except json.JSONDecodeError:
        return {}


def redact(text: str, key: str) -> str:
    return text.replace(key, "[REDACTED-KEY]") if key else text


def summarise(answer: dict, key: str) -> dict:
    """What is kept of an answer: the parsed fields, and the raw output only when it could not be parsed."""
    kept = {k: v for k, v in answer.items() if k not in ("stdout", "stderr")}
    if "reply" not in answer and "error" not in answer:
        kept["stdout_tail"] = redact(answer.get("stdout", ""), key)[-300:]
        kept["stderr_tail"] = redact(answer.get("stderr", ""), key)[-300:]
    return json.loads(redact(json.dumps(kept), key))


def write(path: Path, data: object, key: str) -> None:
    path.write_text(
        redact(json.dumps(data, indent=2, ensure_ascii=False), key) + "\n", encoding="utf-8"
    )


def build_feedback(results: list[dict], by_id: dict, key: str) -> dict:
    """The failure evidence given to the coding agent: request, ground truth, every reply, the rules fired."""
    failed = []
    for result in results:
        if result["score"] >= scoring.PERFECT:
            continue
        failed.append(
            {
                "case": by_id[result["id"]],
                "score": result["score"],
                "repetitions": [
                    {
                        "answer": summarise(r["answer"], key),
                        "layer1": r["layer1"],
                        "layer2": r["layer2"],
                        "layer3": r["layer3"],
                    }
                    for r in result["repetitions"]
                ],
            }
        )
    return {"failed_cases": failed}


def next_run_id(base: Path) -> str:
    taken = [
        int(p.name.split("-")[1]) for p in base.glob("run-*") if p.name.split("-")[1].isdigit()
    ]
    return f"run-{max(taken, default=0) + 1}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    parser.add_argument("--out", default=str(ROOT / "evidence" / "eval-runs"))
    parser.add_argument("--cases")
    parser.add_argument(
        "--app-command",
        help="start another program instead of the application (for tests of the harness)",
    )
    parser.add_argument(
        "--skip-prechecks", action="store_true", help="only for tests of the harness"
    )
    parser.add_argument(
        "--interval",
        type=float,
        help="seconds to pause between model calls (default: threshold.json)",
    )
    args = parser.parse_args()

    threshold = json.loads((HERE / "threshold.json").read_text(encoding="utf-8"))
    cases = dataset.load()
    if args.cases:
        cases = [c for c in cases if c["id"] in args.cases.split(",")]
    by_id = {c["id"]: c for c in cases}
    app = shlex.split(args.app_command) if args.app_command else DEFAULT_APP
    key = load_key()
    base = Path(args.out)
    base.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or next_run_id(base)
    folder = base / run_id
    folder.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    pause = threshold["min_interval_seconds"] if args.interval is None else args.interval

    gates = [] if args.skip_prechecks else prechecks.run_all(folder)
    write(folder / "prechecks.json", gates, key)
    failed_gates = [g for g in gates if g["status"] == "FAIL"]
    for gate in gates:
        print(f"{gate['status']} {gate['name']}")
    if failed_gates:
        write(folder / "feedback.json", {"failed_gates": failed_gates}, key)
        write(
            folder / "eval-results.json",
            {
                "run_id": run_id,
                "verdict": "FAIL",
                "stopped": "pre-checks failed, no model call was made",
            },
            key,
        )
        print("FAIL (pre-checks)")
        return 1

    results = []
    for case in cases:
        answers = []
        for _ in range(threshold["repetitions"]):
            answer = run_app(app, case, key, threshold["call_timeout_seconds"])
            answers.append(answer)
            if answer.get("model_calls"):
                time.sleep(pause)
        judged = scoring.judge_case(
            case, answers, threshold["weights"], [key, threshold["marker_phrase"]]
        )
        results.append(judged)
        print(f"{case['id']} {judged['score']:.3f}")

    values = scoring.metrics(results)
    result_verdict = scoring.verdict(values, threshold)
    info = app_info(app)
    output = {
        "run_id": run_id,
        "verdict": result_verdict,
        "duration_seconds": round(time.monotonic() - started, 1),
        "app_info": info,
        "prechecks": "skipped" if args.skip_prechecks else "passed",
        "threshold": threshold,
        "metrics": values,
        "cases": [
            {
                "id": r["id"], "guardrail": r["guardrail"], "score": r["score"], "stable": r["stable"],
                "repetitions": [
                    {"answer": summarise(x["answer"], key), "layer1": x["layer1"], "layer2": x["layer2"], "layer3": x["layer3"]}
                    for x in r["repetitions"]
                ],
            }
            for r in results
        ],
    }  # fmt: skip
    write(folder / "eval-results.json", output, key)
    feedback = build_feedback(results, by_id, key)
    if feedback["failed_cases"]:
        write(folder / "feedback.json", feedback, key)
    (folder / "summary.txt").write_text(
        "\n".join(f"{k} {v}" for k, v in values.items()) + f"\n{result_verdict}\n", encoding="utf-8"
    )
    print(json.dumps(values), result_verdict)
    return 0 if result_verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
