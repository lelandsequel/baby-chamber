"""Score chain integrity — LUNA-mini."""
from __future__ import annotations
from .canonical import CanonicalState

def score_world(state: CanonicalState, facts) -> dict:
    broken = [x for x in facts if x.startswith("BROKEN_LINK") or x.startswith("HASH_MISMATCH")]
    return {"entry_count": len(state.entries), "broken_links": broken, "intact": "CHAIN_INTACT" in facts}
