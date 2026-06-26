"""Derive drift facts — CONSTELLATION-mini."""
from __future__ import annotations

from .canonical import CanonicalState


def derive_facts(state: CanonicalState) -> frozenset[str]:
    f: set[str] = set()
    if state.reanchor_requested:
        f.add("REANCHOR_REQUESTED")
    if state.baseline_vector:
        f.add("HAS_BASELINE")
    else:
        f.add("NO_BASELINE")
    if state.sample_vector:
        f.add("HAS_SAMPLE")
    else:
        f.add("NO_SAMPLE")
    # signed bedrock validity checked in scoring; facts mirror scores
    return frozenset(f)
