"""Canonical citation claim — GAVEL-mini."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class CanonicalState:
    claim_id: str
    quote: str
    source_id: str
    raw: dict

def canonicalize(raw_request: dict) -> CanonicalState:
    raw = raw_request if isinstance(raw_request, dict) else {}
    return CanonicalState(
        claim_id=str(raw.get("claim_id", raw.get("id", "claim"))),
        quote=str(raw.get("quote", "")).strip(),
        source_id=str(raw.get("source_id", raw.get("source", ""))).strip(),
        raw=raw,
    )
