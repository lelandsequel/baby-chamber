from __future__ import annotations
from .canonical import CanonicalState
from .facts import PATTERNS

def score_world(state: CanonicalState, facts) -> dict:
    findings = sorted(x.replace("SMELL_", "") for x in facts if x.startswith("SMELL_"))
    return {"findings": findings, "patterns_checked": len(PATTERNS), "finding_count": len(findings)}
