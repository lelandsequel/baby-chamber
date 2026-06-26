"""Derive check facts — AURORA-mini."""
from __future__ import annotations

from .canonical import CanonicalState

CONFIG = {"min_checks": 1}


def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
    f: set[str] = set()
    if not state.checks:
        f.add("NO_CHECKS")
    else:
        f.add("HAS_CHECKS")
    failed = [c.name for c in state.checks if not c.passed]
    if failed:
        f.add("HAS_FAILURES")
        f.add(f"FAIL_COUNT_{len(failed)}")
    else:
        f.add("ALL_PASSED")
    if len(state.checks) >= config["min_checks"]:
        f.add("MIN_CHECKS_MET")
    return frozenset(f)
