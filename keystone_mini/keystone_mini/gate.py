"""Integrity gate — refuse CLOSE unless all receipts valid."""
from __future__ import annotations

from dataclasses import dataclass

from .canonical import CanonicalState
from .policy import CloseDecision

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


def _fallback(state: CanonicalState, scores, why: str) -> FinalDecision:
    return FinalDecision(
        "CLOSE_REFUSED",
        {
            "close_id": state.close_id,
            "missing_stages": scores.get("missing_stages", []),
            "invalid_stages": scores.get("invalid_stages", []),
        },
        "fallback after refusal",
        REFUSED,
        why,
    )


def gate(candidate: CloseDecision, state: CanonicalState, facts, scores) -> FinalDecision:
    why = ""
    if candidate.outcome == "CLOSE" and not scores.get("all_valid"):
        missing = scores.get("missing_stages", [])
        invalid = scores.get("invalid_stages", [])
        if missing:
            why = f"CLOSE blocked: missing upstream receipts for {missing}"
        elif invalid:
            why = f"CLOSE blocked: invalid receipt hash for {invalid}"
        else:
            why = "CLOSE blocked: upstream integrity check failed"
    if not why:
        return FinalDecision(
            candidate.outcome,
            candidate.payload,
            candidate.reason,
            RELEASED,
            "",
            candidate.outcome,
        )
    fb = _fallback(state, scores, why)
    fb.candidate_outcome = candidate.outcome
    return fb
