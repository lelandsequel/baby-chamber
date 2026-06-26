"""Derive spine facts — COSMIC-mini."""
from __future__ import annotations

from .canonical import CanonicalState

CONFIG = {"min_values": 1, "min_checks": 1}


def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
    f: set[str] = set()
    if state.generated:
        f.add("SYNTHETIC_GENERATED")
    if state.values:
        f.add("HAS_VALUES")
    else:
        f.add("NO_VALUES")
    if len(state.values) >= config["min_values"]:
        f.add("MIN_VALUES_MET")
    if state.checks:
        f.add("HAS_CHECKS")
    else:
        f.add("NO_CHECKS")
    failed = [c.name for c in state.checks if not c.passed]
    if failed:
        f.add("HAS_CHECK_FAILURES")
    elif state.checks:
        f.add("ALL_CHECKS_PASS")
    if state.prev_hash:
        f.add("HAS_WITNESS_CHAIN")
    if (
        "MIN_VALUES_MET" in f
        and "ALL_CHECKS_PASS" in f
        and "HAS_WITNESS_CHAIN" in f
    ):
        f.add("SPINE_READY")
    return frozenset(f)
