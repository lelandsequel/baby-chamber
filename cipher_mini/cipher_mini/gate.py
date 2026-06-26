from __future__ import annotations
from dataclasses import dataclass
from .canonical import CanonicalState
from .policy import ValueDecision

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

def gate(candidate: ValueDecision, state: CanonicalState, facts) -> FinalDecision:
    why = ""
    if candidate.outcome == "VALUE" and "ALL_SOURCED" not in facts:
        why = "DCF refuses missing or unsourced inputs"
    if not why:
        return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
    fb = FinalDecision("REFUSE", {"missing": state.missing}, "fallback", REFUSED, why)
    fb.candidate_outcome = candidate.outcome
    return fb
