"""Select drift measure outcome — CONSTELLATION-mini."""
from __future__ import annotations

from dataclasses import dataclass, field

from .canonical import CanonicalState


@dataclass
class MeasureDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""


def select_action(state: CanonicalState, facts, scores) -> MeasureDecision:
    if "REANCHOR_REQUESTED" in facts:
        return MeasureDecision(
            "REANCHOR",
            {"bedrock_id": state.bedrock_id},
            "re-anchor to signed bedrock requested (will be gated)",
        )
    if not scores.get("bedrock_valid"):
        return MeasureDecision("MEASURE_REFUSE", {}, "invalid signed bedrock")
    if scores.get("exceeds_threshold"):
        return MeasureDecision(
            "MEASURE_FLAG",
            {
                "bedrock_id": state.bedrock_id,
                "drift_distance": scores.get("drift_distance", 0.0),
            },
            "drift exceeds threshold (will be gated)",
        )
    return MeasureDecision(
        "MEASURE_OK",
        {
            "bedrock_id": state.bedrock_id,
            "drift_distance": scores.get("drift_distance", 0.0),
        },
        "drift within threshold",
    )
