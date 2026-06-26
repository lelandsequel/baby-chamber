"""Select RELEASE or REFUSE — AURORA-mini."""
from __future__ import annotations

from dataclasses import dataclass, field

from .canonical import CanonicalState


@dataclass
class VerdictDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""


def select_action(state: CanonicalState, facts, scores) -> VerdictDecision:
    if "NO_CHECKS" in facts:
        return VerdictDecision("REFUSE", {"reasons": ["no checks provided"]}, "missing checks")
    if "HAS_FAILURES" in facts:
        return VerdictDecision(
            "RELEASE",
            {"candidate_id": state.candidate_id},
            "attempt release despite failures (will be gated)",
        )
    return VerdictDecision(
        "RELEASE",
        {"candidate_id": state.candidate_id, "passed": scores.get("passed_checks", [])},
        "all checks passed",
    )
