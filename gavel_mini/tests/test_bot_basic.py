import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from gavel_mini.bot import adjudicate, _pipeline_receipt
from gavel_mini.gate import REFUSED
FIX = pathlib.Path(__file__).parent / "fixtures"
def load(n): return json.loads((FIX / n).read_text())

def test_determinism():
    assert adjudicate(load("sample_verified.json")) == adjudicate(load("sample_verified.json"))

def test_verified():
    out = adjudicate(load("sample_verified.json"))
    assert out["outcome"] == "VERIFIED" and out["verdict"] == "RELEASED"

def test_mismatch_refused():
    out = adjudicate(load("sample_mismatch.json"))
    assert out["verdict"] == REFUSED

def test_receipt_stable():
    h1 = _pipeline_receipt(load("sample_verified.json"))["deterministic_receipt_hash"]
    assert h1 == _pipeline_receipt(load("sample_verified.json"))["deterministic_receipt_hash"]

if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")): globals()[n](); print("PASS", n)
