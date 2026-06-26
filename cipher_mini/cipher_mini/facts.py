from __future__ import annotations
from .canonical import CanonicalState, REQUIRED
CONFIG = {}

def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
    f: set[str] = set()
    if state.missing:
        f.add("HAS_MISSING")
        for m in state.missing:
            f.add(f"MISSING_{m}")
    if len(state.inputs) == len(REQUIRED):
        f.add("ALL_SOURCED")
    return frozenset(f)
