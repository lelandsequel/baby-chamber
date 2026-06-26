import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from bifrost_mini.bot import verify, _pipeline_receipt
from bifrost_mini.gate import REFUSED
FIX = pathlib.Path(__file__).parent / "fixtures"
def load(n): return json.loads((FIX / n).read_text())

def test_determinism():
    assert verify(load("sample_match.json")) == verify(load("sample_match.json"))

def test_confirm_on_match():
    out = verify(load("sample_match.json"))
    assert out["outcome"] == "CONFIRM" and out["verdict"] == "RELEASED"

def test_mismatch_denied():
    out = verify(load("sample_mismatch.json"))
    assert out["verdict"] == REFUSED and out["outcome"] == "DENY"

def test_receipt_stable():
    h = _pipeline_receipt(load("sample_match.json"))["deterministic_receipt_hash"]
    assert len(h) == 64

if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")): globals()[n](); print("PASS", n)
