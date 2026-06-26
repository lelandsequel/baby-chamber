import json, pathlib, sys, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from luna_mini.bot import witness, _pipeline_receipt
from luna_mini.facts import _entry_hash
from luna_mini.gate import REFUSED
FIX = pathlib.Path(__file__).parent / "fixtures"
def load(n): return json.loads((FIX / n).read_text())
GENESIS = "0" * 64

def test_determinism():
    assert witness(load("sample_intact.json")) == witness(load("sample_intact.json"))

def test_intact_verifies():
    out = witness(load("sample_intact.json"))
    assert out["outcome"] == "VERIFY" and out["verdict"] == "RELEASED"

def test_broken_refused():
    out = witness(load("sample_broken.json"))
    assert out["verdict"] == REFUSED and out["outcome"] == "REFUSE"

def test_receipt_stable():
    h1 = _pipeline_receipt(load("sample_intact.json"))["deterministic_receipt_hash"]
    h2 = _pipeline_receipt(load("sample_intact.json"))["deterministic_receipt_hash"]
    assert h1 == h2 and len(h1) == 64

if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")): globals()[n](); print("PASS", n)
