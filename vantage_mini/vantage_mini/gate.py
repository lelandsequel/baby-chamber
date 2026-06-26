from __future__ import annotations
from dataclasses import dataclass
from .canonical import CanonicalState
from .policy import ScanDecision

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

def gate(candidate: ScanDecision, state: CanonicalState, facts) -> FinalDecision:
    why = ""
    if candidate.outcome == "CLEAN" and "ALL_PATTERNS_CHECKED" not in facts:
        why = "cannot claim CLEAN without checking all patterns"
    if not why:
        return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
    fb = FinalDecision("FLAG", {"findings": ["INCOMPLETE_SCAN"]}, "fallback", REFUSED, why)
    fb.candidate_outcome = candidate.outcome
    return fb
