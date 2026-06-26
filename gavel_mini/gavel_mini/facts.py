"""Synthetic citation store — GAVEL-mini."""
from __future__ import annotations
from .canonical import CanonicalState

CONFIG = {}
CITATION_STORE = {
    "syn_case_001": "The court held that synthetic precedent applies.",
    "syn_case_002": "Deterministic verification requires exact quote match.",
    "syn_statute_01": "No value shall be emitted without provenance.",
}

def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
    f: set[str] = set()
    if not state.source_id:
        f.add("MISSING_SOURCE")
        return frozenset(f)
    if state.source_id not in CITATION_STORE:
        f.add("UNKNOWN_SOURCE")
        return frozenset(f)
    f.add("SOURCE_FOUND")
    if state.quote == CITATION_STORE[state.source_id]:
        f.add("QUOTE_MATCHES")
    else:
        f.add("QUOTE_MISMATCH")
    return frozenset(f)
