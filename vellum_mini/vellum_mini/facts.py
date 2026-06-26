"""Derive provenance facts — VELLUM-mini."""
from __future__ import annotations

from .canonical import CanonicalState

CONFIG = {
    "min_sourced_fields": 1,
}


def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
    f: set[str] = set()
    if state.unsourced_fields:
        f.add("HAS_UNSOURCED")
    if state.fields:
        f.add("HAS_SOURCED")
    if len(state.fields) >= config["min_sourced_fields"]:
        f.add("MIN_SOURCED_MET")
    else:
        f.add("MIN_SOURCED_NOT_MET")
    return frozenset(f)