"""Select CLOSE outcome — KEYSTONE-mini."""
from __future__ import annotations

from dataclasses import dataclass, field

from .canonical import CanonicalState


@dataclass
class CloseDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""


def select_action(state: CanonicalState, facts, scores) -> CloseDecision:
    if scores.get("all_valid"):
        return CloseDecision(
            "CLOSE",
            {"close_id": state.close_id, "locked_stages": scores.get("valid_stages", [])},
            "all upstream receipts present and hash-valid",
        )
    if scores.get("missing_stages"):
        return CloseDecision(
            "CLOSE",
            {"close_id": state.close_id},
            "attempt close despite missing receipts (will be gated)",
        )
    return CloseDecision(
        "CLOSE",
        {"close_id": state.close_id},
        "attempt close despite invalid receipt hashes (will be gated)",
    )
