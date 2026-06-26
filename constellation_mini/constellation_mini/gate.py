"""Drift gate — refuse past threshold; never re-anchor."""
from __future__ import annotations

from dataclasses import dataclass

from .canonical import CanonicalState
from .policy import MeasureDecision

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


def _fallback(state: CanonicalState, facts, scores, why: str) -> FinalDecision:
    return FinalDecision(
        "DRIFT_REFUSED",
        {
            "bedrock_id": state.bedrock_id,
            "drift_distance": scores.get("drift_distance", 0.0),
            "threshold": state.threshold,
        },
        "fallback after refusal",
        REFUSED,
        why,
    )


def gate(candidate: MeasureDecision, state: CanonicalState, facts, scores) -> FinalDecision:
    why = ""
    if candidate.outcome == "REANCHOR":
        why = "REANCHOR blocked: re-anchor to signed bedrock is never permitted"
    elif candidate.outcome == "MEASURE_FLAG":
        why = f"drift {scores.get('drift_distance')} exceeds threshold {state.threshold}"
    elif candidate.outcome == "MEASURE_REFUSE":
        why = "signed bedrock hash or signature invalid"
    elif "NO_BASELINE" in facts or "NO_SAMPLE" in facts:
        why = "measurement requires baseline and sample vectors"

    if not why:
        return FinalDecision(
            candidate.outcome,
            candidate.payload,
            candidate.reason,
            RELEASED,
            "",
            candidate.outcome,
        )
    fb = _fallback(state, facts, scores, why)
    fb.candidate_outcome = candidate.outcome
    return fb
