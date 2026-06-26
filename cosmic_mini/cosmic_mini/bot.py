"""COSMIC-mini: trust-shell spine — produce → vellum → aurora → luna → receipt."""
from __future__ import annotations

import hashlib
import json

from .canonical import canonicalize
from .facts import derive_facts
from .gate import REFUSED, RELEASED, gate
from .policy import select_action
from .receipts import make_receipt
from .scoring import score_world


def _receipt_hash(core: dict) -> str:
    return hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _stage_vellum(state) -> dict:
    """Inline VELLUM — provenance envelope."""
    envelopes = [
        {"name": v.name, "value": v.value, "source": v.source, "sha": v.sha}
        for v in state.values
    ]
    outcome = "ENVELOPE_EMIT" if envelopes else "REFUSED_UNSOURCED"
    return {
        "stage": "vellum",
        "outcome": outcome,
        "envelope_count": len(envelopes),
        "envelopes": envelopes,
    }


def _stage_aurora(state, vellum: dict) -> dict:
    """Inline AURORA — verdict gate."""
    failed = [c.name for c in state.checks if not c.passed]
    if vellum["outcome"] != "ENVELOPE_EMIT":
        outcome = "REFUSE"
    elif failed:
        outcome = "REFUSE"
    elif not state.checks:
        outcome = "REFUSE"
    else:
        outcome = "RELEASE"
    return {
        "stage": "aurora",
        "outcome": outcome,
        "failed_checks": failed,
        "envelope_count": vellum.get("envelope_count", 0),
    }


def _stage_luna(state, aurora: dict) -> dict:
    """Inline LUNA — append-only hash-chain witness."""
    payload = {
        "aurora_outcome": aurora["outcome"],
        "run_id": state.run_id,
        "envelope_count": aurora.get("envelope_count", 0),
    }
    payload_hash = _receipt_hash(payload)
    entry_core = {
        "chain_id": state.chain_id,
        "entry_index": state.entry_index,
        "payload_hash": payload_hash,
        "prev_hash": state.prev_hash,
    }
    entry_hash = _receipt_hash(entry_core)
    return {
        "stage": "luna",
        "outcome": "WITNESSED" if aurora["outcome"] == "RELEASE" else "WITNESS_REFUSED",
        "chain_id": state.chain_id,
        "entry_hash": entry_hash,
        "prev_hash": state.prev_hash,
        "payload_hash": payload_hash,
    }


def _execute_spine(state) -> dict:
    produce = {"stage": "produce", "outcome": "PRODUCED", "value_count": len(state.values)}
    vellum = _stage_vellum(state)
    aurora = _stage_aurora(state, vellum)
    luna = _stage_luna(state, aurora)
    return {"produce": produce, "vellum": vellum, "aurora": aurora, "luna": luna}


def _pipeline_receipt(raw_request: dict) -> dict:
    state = canonicalize(raw_request)
    facts = derive_facts(state)
    scores = score_world(state, facts)
    candidate = select_action(state, facts, scores)
    final = gate(candidate, state, facts)
    trace = _execute_spine(state) if final.verdict == RELEASED else {}
    return make_receipt(state, facts, scores, candidate, final, trace)


def run(raw_request: dict) -> dict:
    receipt = _pipeline_receipt(raw_request)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    state = canonicalize(raw_request)
    facts = derive_facts(state)
    scores = score_world(state, facts)
    candidate = select_action(state, facts, scores)
    final = gate(candidate, state, facts)
    if final.verdict != RELEASED:
        return final.to_response()
    trace = _execute_spine(state)
    return {
        "outcome": final.outcome,
        "payload": {**final.payload, "spine": trace},
        "reason": final.reason,
        "verdict": final.verdict,
    }
