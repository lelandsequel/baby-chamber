from __future__ import annotations
from .canonical import CanonicalState

def score_world(state: CanonicalState, facts) -> dict:
    keys = sorted(state.claim.keys())
    matched = sum(1 for k in keys if state.evidence.get(k) == state.claim[k])
    return {"keys_checked": len(keys), "matched": matched, "match_ratio": round(matched / max(len(keys), 1), 6)}
