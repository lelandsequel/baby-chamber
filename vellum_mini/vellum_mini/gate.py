"""Validation gate — refuse unsourced values."""
from __future__ import annotations

from dataclasses import dataclass

from .canonical import CanonicalState
from .policy import EnvelopeDecision

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
    return FinalDecision(
        "REFUSED_UNSOURCED",
        {"refused_fields": sorted(state.unsourced_fields)},
        "fallback after refusal",
        REFUSED,
        why,
    )


def gate(candidate: EnvelopeDecision, state: CanonicalState, facts) -> FinalDecision:
    why = ""
    if candidate.outcome == "ENVELOPE_EMIT" and "HAS_UNSOURCED" in facts:
        why = "cannot emit envelope with unsourced values"
    elif candidate.outcome == "ENVELOPE_EMIT" and not candidate.payload.get("envelopes"):
        why = "ENVELOPE_EMIT requires at least one envelope"

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