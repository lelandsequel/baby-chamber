import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from cipher_mini.bot import value, _pipeline_receipt
from cipher_mini.gate import REFUSED
FIX = pathlib.Path(__file__).parent / "fixtures"
def load(n): return json.loads((FIX / n).read_text())

def test_determinism():
    assert value(load("sample_complete.json")) == value(load("sample_complete.json"))

def test_complete_values():
    out = value(load("sample_complete.json"))
    assert out["outcome"] == "VALUE" and out["verdict"] == "RELEASED"
    assert out["payload"]["valuation"] > 0

def test_missing_refused():
    out = value(load("sample_missing.json"))
    assert out["verdict"] == REFUSED and out["outcome"] == "REFUSE"

def test_receipt_stable():
    h = _pipeline_receipt(load("sample_complete.json"))["deterministic_receipt_hash"]
    assert h == _pipeline_receipt(load("sample_complete.json"))["deterministic_receipt_hash"]

if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")): globals()[n](); print("PASS", n)
