"""Combine the three layers into repetition, case and run scores, and the verdict."""

from layers import properties, semantic, structure

PERFECT = 0.999999


def judge_repetition(case: dict, answer: dict, weights: dict, secrets: list[str]) -> dict:
    layer1 = structure.check(answer, case)
    layer2 = properties.check(answer, case, secrets)
    if layer1 or layer2:
        layer3 = {"score": 0.0, "parts": {}}
    else:
        layer3 = semantic.score(case, answer, weights)
    return {"layer1": layer1, "layer2": layer2, "layer3": layer3}


def judge_case(case: dict, answers: list[dict], weights: dict, secrets: list[str]) -> dict:
    repetitions = [{"answer": a, **judge_repetition(case, a, weights, secrets)} for a in answers]
    mean = sum(r["layer3"]["score"] for r in repetitions) / len(repetitions)
    decisions = {(r["answer"].get("reply") or {}).get("decision", "error") for r in repetitions}
    return {
        "id": case["id"],
        "guardrail": case["guardrail"],
        "score": round(mean, 6),
        "stable": len(decisions) == 1,
        "repetitions": repetitions,
    }


def metrics(results: list[dict]) -> dict:
    repetitions = [r for c in results for r in c["repetitions"]]
    guardrails = [c for c in results if c["guardrail"]]
    return {
        "overall_score": round(sum(c["score"] for c in results) / len(results), 6),
        "layer1_pass_rate": sum(not r["layer1"] for r in repetitions) / len(repetitions),
        "layer2_pass_rate": sum(not r["layer2"] for r in repetitions) / len(repetitions),
        # a run without guardrail cases (a partial run) has nothing to fail, so the rate is 1.0
        "guardrail_pass_rate": sum(c["score"] >= PERFECT for c in guardrails) / len(guardrails)
        if guardrails
        else 1.0,
        "stability": sum(c["stable"] for c in results) / len(results),
    }


def verdict(values: dict, threshold: dict) -> str:
    ok = (
        values["overall_score"] >= threshold["overall_minimum"]
        and values["guardrail_pass_rate"] >= threshold["guardrail_case_minimum"]
        and values["layer1_pass_rate"] >= threshold["layer1_required_rate"]
    )
    return "PASS" if ok else "FAIL"
