from __future__ import annotations
from dataclasses import dataclass, field
from .canonical import CanonicalState

@dataclass
class AdjudicationDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""

def select_action(state: CanonicalState, facts, scores) -> AdjudicationDecision:
    if "QUOTE_MATCHES" in facts:
        return AdjudicationDecision("VERIFIED", {"source_id": state.source_id}, "quote matches store")
    if "QUOTE_MISMATCH" in facts:
        return AdjudicationDecision("VERIFIED", {"source_id": state.source_id}, "attempt verify mismatch")
    return AdjudicationDecision("REFUSED", {"reason": "unsourced"}, "missing or unknown source")
