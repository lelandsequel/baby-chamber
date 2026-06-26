"""Canonical hash-chain — LUNA-mini."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class ChainEntry:
    index: int
    prev_hash: str
    payload: dict
    entry_hash: str
    raw: dict = field(default_factory=dict)

@dataclass
class CanonicalState:
    chain_id: str
    entries: list[ChainEntry]
    raw: dict

def canonicalize(raw_request: dict) -> CanonicalState:
    raw = raw_request if isinstance(raw_request, dict) else {}
    cid = str(raw.get("chain_id", raw.get("id", "chain")))
    items = raw.get("entries", [])
    entries: list[ChainEntry] = []
    if isinstance(items, list):
        for i, e in enumerate(items):
            if not isinstance(e, dict):
                continue
            entries.append(ChainEntry(
                index=int(e.get("index", i)),
                prev_hash=str(e.get("prev_hash", "")),
                payload=e.get("payload", {}) if isinstance(e.get("payload"), dict) else {},
                entry_hash=str(e.get("entry_hash", "")),
                raw=e,
            ))
    entries.sort(key=lambda x: x.index)
    return CanonicalState(chain_id=cid, entries=entries, raw=raw)
