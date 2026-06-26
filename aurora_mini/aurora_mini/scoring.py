"""Score check results — AURORA-mini."""
from __future__ import annotations

from .canonical import CanonicalState


def score_world(state: CanonicalState, facts) -> dict:
    failed = [c.name for c in state.checks if not c.passed]
    passed = [c.name for c in state.checks if c.passed]
    return {
        "passed_checks": passed,
        "failed_checks": failed,
        "pass_count": len(passed),
        "fail_count": len(failed),
    }
