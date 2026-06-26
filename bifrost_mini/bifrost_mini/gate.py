from __future__ import annotations
from dataclasses import dataclass
from .canonical import CanonicalState
from .policy import VerifyDecision

RELEASED = "RELEASED"
REFUSED = "REFUSED_WITH_FALLBACK"

@dataclass
class FinalDecision:
    outcome: str
    payload: dict
    reason: str
    verdict: str = RELEASED
    refusal_reason: str = ""
    candidate_outcome: str = ""
    def to_response(self) -> dict:
        return {"outcome": self.outcome, "payload": self.payload, "reason": self.reason, "verdict": self.verdict}

def gate(candidate: VerifyDecision, state: CanonicalState, facts) -> FinalDecision:
    why = ""
    if candidate.outcome == "CONFIRM" and "FULL_MATCH" not in facts:
        why = "CONFIRM requires full claim-evidence match"
    if not why:
        return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
    fb = FinalDecision("DENY", {"claim_id": state.claim_id, "match_ratio": 0}, "fallback", REFUSED, why)
    fb.candidate_outcome = candidate.outcome
    return fb
