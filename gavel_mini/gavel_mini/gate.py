from __future__ import annotations
from dataclasses import dataclass
from .canonical import CanonicalState
from .policy import AdjudicationDecision

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

def gate(candidate: AdjudicationDecision, state: CanonicalState, facts) -> FinalDecision:
    why = ""
    if candidate.outcome == "VERIFIED" and "QUOTE_MATCHES" not in facts:
        why = "VERIFIED requires exact quote match"
    if not why:
        return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
    fb = FinalDecision("REFUSED", {"source_id": state.source_id}, "fallback", REFUSED, why)
    fb.candidate_outcome = candidate.outcome
    return fb
