from __future__ import annotations
from dataclasses import dataclass, field
from .canonical import CanonicalState

@dataclass
class VerifyDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""

def select_action(state: CanonicalState, facts, scores) -> VerifyDecision:
    if "FULL_MATCH" in facts:
        return VerifyDecision("CONFIRM", {"claim_id": state.claim_id, "match_ratio": scores["match_ratio"]}, "claim matches evidence")
    if "HAS_MISMATCHES" in facts:
        return VerifyDecision("CONFIRM", {"claim_id": state.claim_id}, "attempt confirm despite mismatch")
    return VerifyDecision("DENY", {"claim_id": state.claim_id}, "missing claim or evidence")
