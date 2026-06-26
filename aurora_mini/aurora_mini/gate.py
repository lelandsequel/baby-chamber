"""Verdict gate — release or refuse-with-fallback."""
from __future__ import annotations

from dataclasses import dataclass

from .canonical import CanonicalState
from .policy import VerdictDecision

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
        return {
            "outcome": self.outcome,
            "payload": self.payload,
            "reason": self.reason,
            "verdict": self.verdict,
        }


def _fallback(state: CanonicalState, facts, why: str) -> FinalDecision:
    reasons = [c.name for c in state.checks if not c.passed] or ["no_checks"]
    return FinalDecision("REFUSE", {"reasons": reasons}, "fallback after refusal", REFUSED, why)


def gate(candidate: VerdictDecision, state: CanonicalState, facts) -> FinalDecision:
    why = ""
    if candidate.outcome == "RELEASE" and "HAS_FAILURES" in facts:
        why = "RELEASE blocked: check failures present"
    elif candidate.outcome == "RELEASE" and "NO_CHECKS" in facts:
        why = "RELEASE blocked: no checks"

    if not why:
        return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
    fb = _fallback(state, facts, why)
    fb.candidate_outcome = candidate.outcome
    return fb
