"""Decide witness outcome — LUNA-mini."""
from __future__ import annotations
from dataclasses import dataclass, field
from .canonical import CanonicalState

@dataclass
class WitnessDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""

def select_action(state: CanonicalState, facts, scores) -> WitnessDecision:
    if "EMPTY_CHAIN" in facts:
        return WitnessDecision("REFUSE", {"reason": "empty chain"}, "no entries")
    if "CHAIN_INTACT" in facts:
        return WitnessDecision("VERIFY", {"chain_id": state.chain_id, "length": len(state.entries)}, "chain intact")
    return WitnessDecision("VERIFY", {"chain_id": state.chain_id}, "attempt verify broken chain")
