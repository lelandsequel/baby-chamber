import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from constellation_mini.bot import _pipeline_receipt, measure
from constellation_mini.canonical import canonicalize
from constellation_mini.facts import derive_facts
from constellation_mini.gate import REFUSED, gate
from constellation_mini.policy import MeasureDecision, select_action
from constellation_mini.scoring import score_world
FIX = pathlib.Path(__file__).parent / "fixtures"

def load(n):
    return json.loads((FIX / n).read_text())

def test_determinism():
    assert measure(load("sample_within_threshold.json")) == measure(load("sample_within_threshold.json"))

def test_within_threshold_ok():
    out = measure(load("sample_within_threshold.json"))
    assert out["outcome"] == "MEASURE_OK"
    assert out["verdict"] == "RELEASED"

def test_exceeds_threshold_refused():
    out = measure(load("sample_exceeds_threshold.json"))
    assert out["verdict"] == REFUSED
    assert out["outcome"] == "DRIFT_REFUSED"

def test_reanchor_always_refused():
    out = measure(load("sample_reanchor_request.json"))
    assert out["verdict"] == REFUSED
    assert "re-anchor" in out["reason"].lower() or out["outcome"] == "DRIFT_REFUSED"

def test_receipt_stable():
    h1 = _pipeline_receipt(load("sample_within_threshold.json"))["deterministic_receipt_hash"]
    h2 = _pipeline_receipt(load("sample_within_threshold.json"))["deterministic_receipt_hash"]
    assert h1 == h2 and len(h1) == 64

if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")):
        globals()[n]()
        print("PASS", n)
