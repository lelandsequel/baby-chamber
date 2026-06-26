from __future__ import annotations
from dataclasses import dataclass
from .canonical import CanonicalState
from .policy import SpecDecision

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

def gate(candidate: SpecDecision, state: CanonicalState, facts) -> FinalDecision:
    why = ""
    if candidate.outcome == "EMIT_SPEC" and ("GOALS_MISSING" in facts or "MISSING_TITLE" in facts):
        why = "spec generation refused: incomplete intent"
    if not why:
        return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
    fb = FinalDecision("REFUSE", {"intent_id": state.intent_id}, "fallback", REFUSED, why)
    fb.candidate_outcome = candidate.outcome
    return fb
