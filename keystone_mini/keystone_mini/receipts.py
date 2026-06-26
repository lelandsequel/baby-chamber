"""Deterministic receipts — KEYSTONE-mini."""
from __future__ import annotations

import hashlib
import json


def make_receipt(state, facts, scores, candidate, final) -> dict:
    core = {
        "close_id": state.close_id,
        "facts": sorted(facts),
        "required_stages": state.required_stages,
        "valid_stages": scores.get("valid_stages", []),
        "invalid_stages": scores.get("invalid_stages", []),
        "missing_stages": scores.get("missing_stages", []),
        "candidate_outcome": candidate.outcome,
        "final_outcome": final.outcome,
        "verdict": final.verdict,
        "refusal_reason": final.refusal_reason or None,
    }
    digest = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**core, "deterministic_receipt_hash": digest}
