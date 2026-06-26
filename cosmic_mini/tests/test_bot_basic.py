import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from cosmic_mini.bot import _pipeline_receipt, run
from cosmic_mini.canonical import canonicalize
from cosmic_mini.facts import derive_facts
from cosmic_mini.gate import REFUSED, gate
from cosmic_mini.policy import SpineDecision, select_action
from cosmic_mini.scoring import score_world
FIX = pathlib.Path(__file__).parent / "fixtures"

def load(n):
    return json.loads((FIX / n).read_text())

def test_determinism():
    assert run(load("sample_spine_ok.json")) == run(load("sample_spine_ok.json"))

def test_spine_completes():
    out = run(load("sample_spine_ok.json"))
    assert out["outcome"] == "SPINE_COMPLETE"
    assert out["verdict"] == "RELEASED"
    assert "spine" in out["payload"]
    assert out["payload"]["spine"]["luna"]["outcome"] == "WITNESSED"

def test_synthetic_generator():
    out = run({"generate": True, "run_id": "synth_001"})
    assert out["outcome"] == "SPINE_COMPLETE"
    assert out["payload"]["spine"]["produce"]["value_count"] >= 1

def test_check_failure_refused():
    st = canonicalize(load("sample_check_fail.json"))
    f = derive_facts(st)
    sc = score_world(st, f)
    c = select_action(st, f, sc)
    fin = gate(c, st, f)
    assert fin.verdict == REFUSED
    assert fin.outcome == "SPINE_REFUSED"

def test_receipt_stable():
    h1 = _pipeline_receipt(load("sample_spine_ok.json"))["deterministic_receipt_hash"]
    h2 = _pipeline_receipt(load("sample_spine_ok.json"))["deterministic_receipt_hash"]
    assert h1 == h2 and len(h1) == 64

if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")):
        globals()[n]()
        print("PASS", n)
