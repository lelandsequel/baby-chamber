"""Deterministic receipts — VELLUM-mini."""
from __future__ import annotations

import hashlib
import json


def make_receipt(state, facts, scores, candidate, final) -> dict:
    core = {
        "record_id": state.record_id,
        "facts": sorted(facts),
        "envelope_count": scores.get("envelope_count", 0),
        "refused_count": scores.get("refused_count", 0),
        "candidate_outcome": candidate.outcome,
        "final_outcome": final.outcome,
        "verdict": final.verdict,
        "refusal_reason": final.refusal_reason or None,
    }
    digest = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**core, "deterministic_receipt_hash": digest}