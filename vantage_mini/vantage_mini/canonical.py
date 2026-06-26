from __future__ import annotations
from dataclasses import dataclass

@dataclass
class CanonicalState:
    file_id: str
    source: str
    raw: dict

def canonicalize(raw_request: dict) -> CanonicalState:
    raw = raw_request if isinstance(raw_request, dict) else {}
    return CanonicalState(
        file_id=str(raw.get("file_id", "file")),
        source=str(raw.get("source", raw.get("code", ""))),
        raw=raw,
    )
