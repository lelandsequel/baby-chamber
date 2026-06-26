"""Deterministic receipts — CONSTELLATION-mini."""
from __future__ import annotations

import hashlib
import json


def make_receipt(state, facts, scores, candidate, final) -> dict:
    core = {
        "bedrock_id": state.bedrock_id,
        "facts": sorted(facts),
        "drift_distance": scores.get("drift_distance", 0.0),
        "threshold": scores.get("threshold", 0.0),
        "bedrock_valid": scores.get("bedrock_valid", False),
        "candidate_outcome": candidate.outcome,
        "final_outcome": final.outcome,
        "verdict": final.verdict,
        "refusal_reason": final.refusal_reason or None,
    }
    digest = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**core, "deterministic_receipt_hash": digest}
