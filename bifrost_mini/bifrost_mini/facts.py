from __future__ import annotations
from .canonical import CanonicalState
CONFIG = {}

def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
    f: set[str] = set()
    if not state.claim:
        f.add("EMPTY_CLAIM")
        return frozenset(f)
    if not state.evidence:
        f.add("EMPTY_EVIDENCE")
        return frozenset(f)
    f.add("HAS_PAIR")
    mismatches = []
    for k, v in sorted(state.claim.items()):
        if k not in state.evidence:
            mismatches.append(k)
        elif state.evidence[k] != v:
            mismatches.append(k)
    if mismatches:
        f.add("HAS_MISMATCHES")
        f.add(f"MISMATCH_COUNT_{len(mismatches)}")
    else:
        f.add("FULL_MATCH")
    return frozenset(f)
