from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class CanonicalState:
    claim_id: str
    claim: dict
    evidence: dict
    raw: dict

def canonicalize(raw_request: dict) -> CanonicalState:
    raw = raw_request if isinstance(raw_request, dict) else {}
    claim = raw.get("claim", {})
    evidence = raw.get("evidence", {})
    return CanonicalState(
        claim_id=str(raw.get("claim_id", "claim")),
        claim=claim if isinstance(claim, dict) else {},
        evidence=evidence if isinstance(evidence, dict) else {},
        raw=raw,
    )
