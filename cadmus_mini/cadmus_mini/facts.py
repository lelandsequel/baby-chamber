from __future__ import annotations
from .canonical import CanonicalState
CONFIG = {"min_goals": 1}

def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
    f: set[str] = set()
    if not state.title:
        f.add("MISSING_TITLE")
    if len(state.goals) >= config["min_goals"]:
        f.add("GOALS_PRESENT")
    else:
        f.add("GOALS_MISSING")
    if state.constraints:
        f.add("HAS_CONSTRAINTS")
    return frozenset(f)
