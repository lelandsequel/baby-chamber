import hashlib, json
def make_receipt(state, facts, scores, candidate, final) -> dict:
    core = {"claim_id": state.claim_id, "facts": sorted(facts), "match_ratio": scores.get("match_ratio"),
            "candidate_outcome": candidate.outcome, "final_outcome": final.outcome,
            "verdict": final.verdict, "refusal_reason": final.refusal_reason or None}
    digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**core, "deterministic_receipt_hash": digest}
