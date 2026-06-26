"""Select spine completion — COSMIC-mini."""
from __future__ import annotations

from dataclasses import dataclass, field

from .canonical import CanonicalState


@dataclass
class SpineDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""


def select_action(state: CanonicalState, facts, scores) -> SpineDecision:
    if "SPINE_READY" in facts:
        return SpineDecision(
            "SPINE_COMPLETE",
            {"run_id": state.run_id, "stages": ["produce", "vellum", "aurora", "luna"]},
            "all spine preconditions met",
        )
    if "HAS_CHECK_FAILURES" in facts:
        return SpineDecision(
            "SPINE_COMPLETE",
            {"run_id": state.run_id},
            "attempt complete despite check failures (will be gated)",
        )
    if "NO_VALUES" in facts:
        return SpineDecision("SPINE_ABORT", {}, "no producible values")
    return SpineDecision("SPINE_ABORT", {}, "spine preconditions not met")
