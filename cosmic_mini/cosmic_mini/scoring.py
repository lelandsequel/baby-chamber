"""Score spine stages — COSMIC-mini."""
from __future__ import annotations

from .canonical import CanonicalState


def score_world(state: CanonicalState, facts) -> dict:
    failed = [c.name for c in state.checks if not c.passed]
    return {
        "value_count": len(state.values),
        "check_count": len(state.checks),
        "failed_checks": failed,
        "chain_id": state.chain_id,
        "entry_index": state.entry_index,
    }
