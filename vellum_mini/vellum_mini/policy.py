"""Select envelope outcome — VELLUM-mini."""
from __future__ import annotations

from dataclasses import dataclass, field

from .canonical import CanonicalState


@dataclass
class EnvelopeDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""


def select_action(state: CanonicalState, facts, scores) -> EnvelopeDecision:
    if "HAS_UNSOURCED" in facts:
        return EnvelopeDecision(
            "ENVELOPE_EMIT",
            {"envelopes": scores.get("envelopes", [])},
            "attempt emit despite unsourced (will be gated)",
        )
    if "MIN_SOURCED_MET" not in facts:
        return EnvelopeDecision("REFUSE_EMPTY", {}, "no sourced values")
    return EnvelopeDecision(
        "ENVELOPE_EMIT",
        {"envelopes": scores.get("envelopes", [])},
        "all values sourced and sha-verified",
    )