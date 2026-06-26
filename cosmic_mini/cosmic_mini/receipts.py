"""Deterministic receipts — COSMIC-mini."""
from __future__ import annotations

import hashlib
import json


def make_receipt(state, facts, scores, candidate, final, spine_trace: dict | None = None) -> dict:
    core = {
        "run_id": state.run_id,
        "facts": sorted(facts),
        "value_count": scores.get("value_count", 0),
        "check_count": scores.get("check_count", 0),
        "candidate_outcome": candidate.outcome,
        "final_outcome": final.outcome,
        "verdict": final.verdict,
        "refusal_reason": final.refusal_reason or None,
        "spine_trace": spine_trace or {},
    }
    digest = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**core, "deterministic_receipt_hash": digest}
