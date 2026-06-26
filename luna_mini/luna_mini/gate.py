"""Gate broken chains — LUNA-mini."""
from __future__ import annotations
from dataclasses import dataclass
from .canonical import CanonicalState
from .policy import WitnessDecision

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

def gate(candidate: WitnessDecision, state: CanonicalState, facts) -> FinalDecision:
    why = ""
    if candidate.outcome == "VERIFY" and "CHAIN_INTACT" not in facts:
        why = "chain link or hash mismatch detected"
    if not why:
        return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
    fb = FinalDecision("REFUSE", {"broken": [x for x in facts if "BROKEN" in x or "MISMATCH" in x]}, "fallback", REFUSED, why)
    fb.candidate_outcome = candidate.outcome
    return fb
