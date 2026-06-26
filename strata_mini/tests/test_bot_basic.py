"""Acceptance tests for STRATA-mini. Run: PYTHONPATH=. python3 tests/test_bot_basic.py"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from strata_mini.bot import _pipeline_receipt, choose_action
from strata_mini.canonical import canonicalize
from strata_mini.facts import derive_facts
from strata_mini.gate import REFUSED, gate
from strata_mini.policy import ActionDecision, select_action
from strata_mini.receipts import make_receipt
from strata_mini.scoring import score_world

FIX = pathlib.Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text())


def _receipt(raw):
    state = canonicalize(raw)
    facts = derive_facts(state)
    scores = score_world(state, facts)
    candidate = select_action(state, facts, scores)
    final = gate(candidate, state, facts)
    return make_receipt(state, facts, scores, candidate, final)


def test_1_same_input_same_output_twice():
    raw = load("sample_tick_asteroid_visible.json")
    assert choose_action(raw) == choose_action(raw)


def test_2_destroyed_returns_respawn():
    raw = load("sample_tick_empty.json")
    raw["ship"]["destroyed"] = True
    assert choose_action(raw)["action"] == "RESPAWN"


def test_3_low_energy_recharges_or_waits():
    raw = load("sample_tick_low_energy.json")
    assert choose_action(raw)["action"] in ("RECHARGE", "WAIT")


def test_4_at_asteroid_mines_when_not_full():
    raw = load("sample_tick_at_asteroid.json")
    assert choose_action(raw)["action"] == "MINE"


def test_5_cargo_full_moves_toward_trading_post():
    raw = load("sample_tick_cargo_needs_selling.json")
    out = choose_action(raw)
    assert out["action"] == "MOVE"
    assert out["mode"] == "SELL_RUN"


def test_6_invalid_mine_candidate_is_refused_by_gate():
    state = canonicalize(load("sample_tick_empty.json"))  # nowhere near an asteroid
    facts = derive_facts(state)
    bad = ActionDecision("MINE", {}, "forced bad candidate", "MINE_LOCAL")
    final = gate(bad, state, facts)
    assert final.verdict == REFUSED
    assert final.action != "MINE"
    assert final.refusal_reason


def test_7_receipt_hash_is_stable():
    raw = load("sample_tick_at_asteroid.json")
    h1 = _pipeline_receipt(raw)["deterministic_receipt_hash"]
    h2 = _pipeline_receipt(raw)["deterministic_receipt_hash"]
    assert h1 == h2
    assert len(h1) == 64


if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")):
        globals()[n]()
        print("PASS", n)
