from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class CanonicalState:
    intent_id: str
    title: str
    goals: list[str]
    constraints: list[str]
    raw: dict

def canonicalize(raw_request: dict) -> CanonicalState:
    raw = raw_request if isinstance(raw_request, dict) else {}
    goals = raw.get("goals", [])
    constraints = raw.get("constraints", [])
    if not isinstance(goals, list): goals = []
    if not isinstance(constraints, list): constraints = []
    return CanonicalState(
        intent_id=str(raw.get("intent_id", "intent")),
        title=str(raw.get("title", "")).strip(),
        goals=sorted(str(g) for g in goals),
        constraints=sorted(str(c) for c in constraints),
        raw=raw,
    )
