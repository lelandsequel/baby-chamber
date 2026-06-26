"""Spine gate — refuse incomplete spine."""
from __future__ import annotations

from dataclasses import dataclass

from .canonical import CanonicalState
from .policy import SpineDecision

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
    reasons = []
    if "NO_VALUES" in facts:
        reasons.append("no_values")
    if "HAS_CHECK_FAILURES" in facts:
        reasons.extend(c.name for c in state.checks if not c.passed)
    if not reasons:
        reasons.append("spine_not_ready")
    return FinalDecision(
        "SPINE_REFUSED",
        {"run_id": state.run_id, "reasons": sorted(reasons)},
        "fallback after refusal",
        REFUSED,
        why,
    )


def gate(candidate: SpineDecision, state: CanonicalState, facts) -> FinalDecision:
    why = ""
    if candidate.outcome == "SPINE_COMPLETE" and "HAS_CHECK_FAILURES" in facts:
        why = "SPINE_COMPLETE blocked: check failures present"
    elif candidate.outcome == "SPINE_COMPLETE" and "SPINE_READY" not in facts:
        why = "SPINE_COMPLETE blocked: spine not ready"
    if not why:
        return FinalDecision(
            candidate.outcome,
            candidate.payload,
            candidate.reason,
            RELEASED,
            "",
            candidate.outcome,
        )
    fb = _fallback(state, facts, why)
    fb.candidate_outcome = candidate.outcome
    return fb
