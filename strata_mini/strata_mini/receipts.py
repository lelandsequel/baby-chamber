"""Deterministic receipts — STRATA-mini.

A receipt is a small auditable record of why an action was chosen. The hash is
sha256 over a canonical JSON of the receipt core. No timestamps inside the hash,
so the same input + config always produces the same receipt hash.
"""
from __future__ import annotations

import hashlib
import json


def make_receipt(state, facts, scores, candidate, final) -> dict:
    core = {
        "tick": int(state.tick),
        "ship_id": state.ship_id,
        "position": [round(state.position[0], 6), round(state.position[1], 6)],
        "facts": sorted(facts),
        "mode": final.mode,
        "scores_summary": {
            "best_asteroid": scores.get("best_asteroid"),
            "best_trading_post": scores.get("best_trading_post"),
            "explore_direction": scores.get("explore_direction"),
            "asteroid_count": len(scores.get("asteroids", [])),
            "post_count": len(scores.get("trading_posts", [])),
        },
        "candidate_action": candidate.action,
        "final_action": final.action,
        "verdict": final.verdict,
        "refusal_reason": final.refusal_reason or None,
    }
    digest = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**core, "deterministic_receipt_hash": digest}
