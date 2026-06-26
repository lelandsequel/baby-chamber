import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from keystone_mini.bot import _pipeline_receipt, close
from keystone_mini.canonical import canonicalize
from keystone_mini.facts import derive_facts
from keystone_mini.gate import REFUSED, gate
from keystone_mini.policy import CloseDecision, select_action
from keystone_mini.scoring import score_world, verify_receipt
FIX = pathlib.Path(__file__).parent / "fixtures"

def load(n):
    return json.loads((FIX / n).read_text())

def test_determinism():
    assert close(load("sample_all_valid.json")) == close(load("sample_all_valid.json"))

def test_all_valid_closes():
    out = close(load("sample_all_valid.json"))
    assert out["outcome"] == "CLOSE"
    assert out["verdict"] == "RELEASED"

def test_missing_receipt_refused():
    out = close(load("sample_missing_receipt.json"))
    assert out["verdict"] == REFUSED
    assert out["outcome"] == "CLOSE_REFUSED"

def test_invalid_hash_refused():
    out = close(load("sample_invalid_hash.json"))
    assert out["verdict"] == REFUSED

def test_verify_receipt():
    rec = load("sample_all_valid.json")["upstream_receipts"]["vellum"]
    assert verify_receipt(rec)

def test_receipt_stable():
    h1 = _pipeline_receipt(load("sample_all_valid.json"))["deterministic_receipt_hash"]
    h2 = _pipeline_receipt(load("sample_all_valid.json"))["deterministic_receipt_hash"]
    assert h1 == h2 and len(h1) == 64

if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")):
        globals()[n]()
        print("PASS", n)
