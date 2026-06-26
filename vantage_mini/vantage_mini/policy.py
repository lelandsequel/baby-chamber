from __future__ import annotations
from dataclasses import dataclass, field
from .canonical import CanonicalState

@dataclass
class ScanDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""

def select_action(state: CanonicalState, facts, scores) -> ScanDecision:
    if "HAS_FINDINGS" in facts:
        return ScanDecision("FLAG", {"findings": scores["findings"]}, "smells detected")
    return ScanDecision("CLEAN", {}, "no smells in checked patterns")
