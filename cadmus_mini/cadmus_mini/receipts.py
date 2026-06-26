import hashlib, json
def make_receipt(state, facts, scores, candidate, final) -> dict:
    spec = candidate.payload.get("spec", {})
    core = {"intent_id": state.intent_id, "facts": sorted(facts), "section_count": scores.get("section_count", 0),
            "spec_title": spec.get("title"), "candidate_outcome": candidate.outcome,
            "final_outcome": final.outcome, "verdict": final.verdict, "refusal_reason": final.refusal_reason or None}
    digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**core, "deterministic_receipt_hash": digest}
