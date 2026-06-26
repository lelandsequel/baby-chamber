"""CONSTELLATION-mini: drift distance from signed bedrock."""
from __future__ import annotations

import json

from .canonical import canonicalize
from .facts import derive_facts
from .gate import gate
from .policy import select_action
from .receipts import make_receipt
from .scoring import score_world


def _pipeline_receipt(raw_request: dict) -> dict:
    state = canonicalize(raw_request)
    facts = derive_facts(state)
    scores = score_world(state, facts)
    candidate = select_action(state, facts, scores)
    final = gate(candidate, state, facts, scores)
    return make_receipt(state, facts, scores, candidate, final)


def measure(raw_request: dict) -> dict:
    receipt = _pipeline_receipt(raw_request)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    state = canonicalize(raw_request)
    facts = derive_facts(state)
    scores = score_world(state, facts)
    candidate = select_action(state, facts, scores)
    final = gate(candidate, state, facts, scores)
    return final.to_response()
