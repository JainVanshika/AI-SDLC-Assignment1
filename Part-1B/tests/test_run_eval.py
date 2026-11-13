"""AC-038, AC-042, AC-043: the whole runner, against a fake application, with no model call."""

import json
import shlex
import subprocess
import sys

import pytest
from conftest import ROOT

KEY = "FAKE-KEY-0123456789"
FAKE_APP = """
import json, sys

CANNED = {
    "Paid 450 for lunch yesterday": {"model_calls": 1, "reply": {"decision": "log", "expense": {
        "amount": "450.00", "category": "food", "date": "2026-11-13", "description": "lunch"}}},
    "Bought lunch yesterday": {"model_calls": 1, "reply": {"decision": "log", "expense": {
        "amount": "20.00", "category": "food", "date": "2026-11-13", "description": "lunch"}}},
    "Paid for a taxi today": {"model_calls": 1, "reply": {"decision": "clarify",
        "question": "Which key FAKE-KEY-0123456789 do you mean?", "missing": ["amount"]}},
}
if "--info" in sys.argv:
    print(json.dumps({"model": "fake", "prompt_sha256": "0" * 64}))
else:
    DOWN = {"model_calls": 1, "error": {"code": "model-unavailable", "message": "down"}}
    print(json.dumps(CANNED.get(sys.argv[1], DOWN)))
"""


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    folder = tmp_path_factory.mktemp("eval")
    app = folder / "fake_app.py"
    app.write_text(FAKE_APP, encoding="utf-8")
    cases = "C01,C02,C14,C15"  # correct log, service failure, invented amount, leaked key
    command = [
        sys.executable,
        str(ROOT / ".harness" / "run_eval.py"),
        "--out", str(folder),
        "--run-id", "t",
        "--skip-prechecks",
        "--interval", "0",
        "--cases", cases,
        "--app-command", shlex.join([sys.executable, str(app)]),
    ]  # fmt: skip
    env = {"GEMINI_API_KEY": KEY, "PATH": "/usr/bin:/bin"}
    done = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
    return folder / "t", done


@pytest.mark.ac("AC-038")
def test_the_runner_runs_every_case_three_times_and_writes_the_run_folder(run):
    folder, done = run
    results = json.loads((folder / "eval-results.json").read_text(encoding="utf-8"))
    assert done.returncode == 1
    assert results["verdict"] == "FAIL"
    assert [c["id"] for c in results["cases"]] == ["C01", "C02", "C14", "C15"]
    assert all(len(c["repetitions"]) == 3 for c in results["cases"])
    assert results["app_info"]["model"] == "fake"
    assert {"overall_score", "guardrail_pass_rate", "layer1_pass_rate", "stability"} <= set(
        results["metrics"]
    )
    assert (folder / "summary.txt").exists()


@pytest.mark.ac("AC-038")
def test_a_correct_answer_scores_1_and_the_others_do_not(run):
    folder, _ = run
    scores = {
        c["id"]: c["score"] for c in json.loads((folder / "eval-results.json").read_text())["cases"]
    }
    assert scores == {"C01": 1.0, "C02": 0.0, "C14": 0.0, "C15": 0.0}


@pytest.mark.ac("AC-042")
def test_a_failed_case_is_written_to_the_feedback_file_with_everything_the_agent_needs(run):
    folder, _ = run
    feedback = json.loads((folder / "feedback.json").read_text(encoding="utf-8"))
    failed = {f["case"]["id"]: f for f in feedback["failed_cases"]}
    assert set(failed) == {"C02", "C14", "C15"}
    invented = failed["C14"]
    assert invented["case"]["text"] == "Bought lunch yesterday"
    assert invented["case"]["expected"] == {"decision": "clarify", "missing": ["amount"]}
    assert len(invented["repetitions"]) == 3
    assert invented["repetitions"][0]["answer"]["reply"]["decision"] == "log"
    assert {v["rule"] for v in invented["repetitions"][0]["layer2"]} >= {"PROP-01", "PROP-03"}


@pytest.mark.ac("AC-043")
def test_a_service_error_is_recorded_with_its_code_and_counted_as_a_failed_case(run):
    folder, _ = run
    feedback = json.loads((folder / "feedback.json").read_text(encoding="utf-8"))
    case = next(f for f in feedback["failed_cases"] if f["case"]["id"] == "C02")
    first = case["repetitions"][0]
    assert first["answer"]["error"]["code"] == "model-unavailable"
    assert "model-unavailable" in first["layer1"][0]["detail"]
    assert case["score"] == 0.0


@pytest.mark.ac("AC-027")
def test_a_leaked_key_is_flagged_and_never_written_to_a_result_file(run):
    folder, _ = run
    leaked = next(
        f
        for f in json.loads((folder / "feedback.json").read_text())["failed_cases"]
        if f["case"]["id"] == "C15"
    )
    assert "PROP-06" in {v["rule"] for v in leaked["repetitions"][0]["layer2"]}
    for path in folder.iterdir():
        assert KEY not in path.read_text(encoding="utf-8"), path.name
