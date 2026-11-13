"""Layer 3: compare the answer with the ground truth. No model is used as a judge."""


def score(case: dict, answer: dict, weights: dict) -> dict:
    """Score one answer that has passed layers 1 and 2. Wording fields are never compared."""
    expected = case["expected"]
    if expected["decision"] == "error":
        code = (answer.get("error") or {}).get("code")
        ok = code == expected["code"] and answer.get("model_calls") == 0
        return {"score": 1.0 if ok else 0.0, "parts": {"error": ok}}
    reply = answer.get("reply") or {}
    if reply.get("decision") != expected["decision"]:
        return {"score": 0.0, "parts": {"decision": False}}
    w = weights[expected["decision"]]
    parts = {"decision": True}
    total = w["decision"]
    if expected["decision"] == "log":
        got = reply["expense"]
        for key in ("amount", "category", "date"):
            parts[key] = got.get(key) == expected[key]
            total += w[key] if parts[key] else 0.0
    elif expected["decision"] == "clarify":
        parts["missing"] = set(reply.get("missing", [])) == set(expected["missing"])
        total += w["missing"] if parts["missing"] else 0.0
    else:
        parts["reason"] = reply.get("reason") == expected["reason"]
        total += w["reason"] if parts["reason"] else 0.0
    return {"score": round(total, 6), "parts": parts}
