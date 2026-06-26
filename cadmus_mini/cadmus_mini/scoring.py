from __future__ import annotations
from .canonical import CanonicalState

def score_world(state: CanonicalState, facts) -> dict:
    sections = []
    if state.title:
        sections.append("title")
    if state.goals:
        sections.append("goals")
    if state.constraints:
        sections.append("constraints")
    return {"section_count": len(sections), "sections": sections}
