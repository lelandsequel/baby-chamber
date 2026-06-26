import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from aurora_mini.bot import _pipeline_receipt, verdict
from aurora_mini.canonical import canonicalize
from aurora_mini.facts import derive_facts
from aurora_mini.gate import REFUSED, gate
from aurora_mini.policy import VerdictDecision, select_action
from aurora_mini.scoring import score_world
FIX = pathlib.Path(__file__).parent / "fixtures"
def load(n): return json.loads((FIX / n).read_text())

def test_determinism():
    assert verdict(load("sample_all_pass.json")) == verdict(load("sample_all_pass.json"))

def test_all_pass_releases():
    out = verdict(load("sample_all_pass.json"))
    assert out["outcome"] == "RELEASE" and out["verdict"] == "RELEASED"

def test_failure_refused():
    st = canonicalize(load("sample_with_failure.json"))
    f = derive_facts(st); sc = score_world(st, f)
    c = select_action(st, f, sc); fin = gate(c, st, f)
    assert fin.verdict == REFUSED and fin.outcome == "REFUSE"

def test_receipt_stable():
    h1 = _pipeline_receipt(load("sample_all_pass.json"))["deterministic_receipt_hash"]
    h2 = _pipeline_receipt(load("sample_all_pass.json"))["deterministic_receipt_hash"]
    assert h1 == h2 and len(h1) == 64

if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")): globals()[n](); print("PASS", n)
