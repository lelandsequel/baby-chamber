import hashlib, json
def make_receipt(state, facts, scores, candidate, final) -> dict:
    core = {"file_id": state.file_id, "facts": sorted(facts), "finding_count": scores.get("finding_count", 0),
            "candidate_outcome": candidate.outcome, "final_outcome": final.outcome,
            "verdict": final.verdict, "refusal_reason": final.refusal_reason or None}
    digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**core, "deterministic_receipt_hash": digest}
