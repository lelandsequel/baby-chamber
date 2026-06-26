"""Deterministic receipts — AURORA-mini."""
from __future__ import annotations

import hashlib
import json


def make_receipt(state, facts, scores, candidate, final) -> dict:
    core = {
        "candidate_id": state.candidate_id,
        "facts": sorted(facts),
        "pass_count": scores.get("pass_count", 0),
        "fail_count": scores.get("fail_count", 0),
        "candidate_outcome": candidate.outcome,
        "final_outcome": final.outcome,
        "verdict": final.verdict,
        "refusal_reason": final.refusal_reason or None,
    }
    digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**core, "deterministic_receipt_hash": digest}
