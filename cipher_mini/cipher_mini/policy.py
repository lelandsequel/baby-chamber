from __future__ import annotations
from dataclasses import dataclass, field
from .canonical import CanonicalState

@dataclass
class ValueDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""

def select_action(state: CanonicalState, facts, scores) -> ValueDecision:
    if "ALL_SOURCED" in facts:
        return ValueDecision("VALUE", {"deal_id": state.deal_id, "valuation": scores["valuation"]}, "dcf complete")
    return ValueDecision("VALUE", {"deal_id": state.deal_id, "valuation": 0}, "attempt value with gaps")
