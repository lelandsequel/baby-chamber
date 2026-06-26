"""Derive integrity facts — KEYSTONE-mini."""
from __future__ import annotations

from .canonical import CanonicalState


def derive_facts(state: CanonicalState) -> frozenset[str]:
    f: set[str] = set()
    present = set(state.upstream_receipts)
    required = set(state.required_stages)
    missing = sorted(required - present)
    if missing:
        f.add("MISSING_RECEIPTS")
        f.add(f"MISSING_COUNT_{len(missing)}")
    else:
        f.add("ALL_RECEIPTS_PRESENT")
    if present:
        f.add("HAS_ANY_RECEIPT")
    return frozenset(f)
