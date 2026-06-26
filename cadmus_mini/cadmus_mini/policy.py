from __future__ import annotations
from dataclasses import dataclass, field
from .canonical import CanonicalState

@dataclass
class SpecDecision:
    outcome: str
    payload: dict = field(default_factory=dict)
    reason: str = ""

def _build_spec(state: CanonicalState) -> dict:
    return {
        "intent_id": state.intent_id,
        "title": state.title,
        "goals": state.goals,
        "constraints": state.constraints,
        "sections": ["overview", "goals", "constraints", "acceptance"],
    }

def select_action(state: CanonicalState, facts, scores) -> SpecDecision:
    if "GOALS_PRESENT" in facts and state.title:
        return SpecDecision("EMIT_SPEC", {"spec": _build_spec(state)}, "intent complete")
    return SpecDecision("EMIT_SPEC", {"spec": {}}, "attempt spec with incomplete intent")
