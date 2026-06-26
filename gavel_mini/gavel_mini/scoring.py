from __future__ import annotations
from .canonical import CanonicalState
from .facts import CITATION_STORE

def score_world(state: CanonicalState, facts) -> dict:
    expected = CITATION_STORE.get(state.source_id, "")
    return {"source_id": state.source_id, "expected_len": len(expected), "quote_len": len(state.quote)}
