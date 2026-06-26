"""Acceptance tests for VELLUM-mini."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from vellum_mini.bot import _pipeline_receipt, envelope
from vellum_mini.canonical import canonicalize
from vellum_mini.facts import derive_facts
from vellum_mini.gate import REFUSED, gate
from vellum_mini.policy import EnvelopeDecision, select_action
from vellum_mini.scoring import score_world

FIX = pathlib.Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text())


def test_determinism_same_input_twice():
    raw = load("sample_sourced.json")
    assert envelope(raw) == envelope(raw)


def test_sourced_values_emit_envelope():
    raw = load("sample_sourced.json")
    out = envelope(raw)
    assert out["outcome"] == "ENVELOPE_EMIT"
    assert out["verdict"] == "RELEASED"
    assert len(out["payload"]["envelopes"]) == 2


def test_unsourced_refused_by_gate():
    state = canonicalize(load("sample_unsourced.json"))
    facts = derive_facts(state)
    scores = score_world(state, facts)
    bad = select_action(state, facts, scores)
    final = gate(bad, state, facts)
    assert final.verdict == REFUSED
    assert final.refusal_reason
    assert final.outcome == "REFUSED_UNSOURCED"


def test_receipt_hash_stable():
    raw = load("sample_sourced.json")
    h1 = _pipeline_receipt(raw)["deterministic_receipt_hash"]
    h2 = _pipeline_receipt(raw)["deterministic_receipt_hash"]
    assert h1 == h2
    assert len(h1) == 64


if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")):
        globals()[n]()
        print("PASS", n)