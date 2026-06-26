"""Verify chain links — LUNA-mini."""
from __future__ import annotations
import hashlib, json
from .canonical import CanonicalState

CONFIG = {"genesis_prev": "0" * 64}

def _entry_hash(prev: str, payload: dict) -> str:
    core = {"prev_hash": prev, "payload": payload}
    return hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
    f: set[str] = set()
    if not state.entries:
        f.add("EMPTY_CHAIN")
        return frozenset(f)
    f.add("HAS_ENTRIES")
    prev = config["genesis_prev"]
    for e in state.entries:
        if e.prev_hash != prev:
            f.add(f"BROKEN_LINK_AT_{e.index}")
            break
        expected = _entry_hash(prev, e.payload)
        if e.entry_hash != expected:
            f.add(f"HASH_MISMATCH_AT_{e.index}")
            break
        prev = e.entry_hash
    else:
        f.add("CHAIN_INTACT")
    return frozenset(f)
