"""Validation gate + safe fallback — STRATA-mini.

Refusal-as-feature: a candidate action that doesn't hold up against the facts is
not silently shipped. It's refused, and a safe fallback is returned with a
recorded reason. The chamber rule, in miniature: release it or refuse it.
"""
from __future__ import annotations

from dataclasses import dataclass

from .canonical import CanonicalState
from .policy import ActionDecision
from .scoring import DIRECTIONS, explore_direction

RELEASED = "RELEASED"
REFUSED = "REFUSED_WITH_FALLBACK"


@dataclass
class FinalDecision:
    action: str
    payload: dict
    mode: str
    reason: str
    verdict: str = RELEASED
    refusal_reason: str = ""
    candidate_action: str = ""

    def to_response(self) -> dict:
        return {
            "action": self.action,
            "payload": self.payload,
            "mode": self.mode,
            "reason": self.reason,
            "verdict": self.verdict,
        }


def _fallback(state: CanonicalState, facts, why: str) -> FinalDecision:
    if "ENERGY_CRITICAL" in facts:
        return FinalDecision("RECHARGE", {}, "RECHARGE", "fallback after refusal", REFUSED, why)
    if "RECHARGING" in facts:
        return FinalDecision("WAIT", {"reason": "charging"}, "WAIT_SAFE", "fallback after refusal", REFUSED, why)
    return FinalDecision("MOVE", {"direction": explore_direction(state)}, "EXPLORE",
                         "fallback after refusal", REFUSED, why)


def gate(candidate: ActionDecision, state: CanonicalState, facts) -> FinalDecision:
    a = candidate.action
    why = ""

    if a == "MINE" and "AT_ASTEROID" not in facts:
        why = "MINE requires AT_ASTEROID"
    elif a == "SELL" and "AT_TRADING_POST" not in facts:
        why = "SELL requires AT_TRADING_POST"
    elif a == "RECHARGE_END" and "RECHARGING" not in facts:
        why = "RECHARGE_END requires RECHARGING"
    elif a == "ATTACK":
        why = "ATTACK not implemented in v1"
    elif a == "MOVE" and candidate.payload.get("direction") not in DIRECTIONS:
        why = "MOVE requires a valid direction"

    if not why:
        return FinalDecision(candidate.action, candidate.payload, candidate.mode,
                             candidate.reason, RELEASED, "", candidate.action)

    fb = _fallback(state, facts, why)
    fb.candidate_action = candidate.action
    return fb
