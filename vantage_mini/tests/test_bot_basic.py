import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from vantage_mini.bot import scan, _pipeline_receipt
FIX = pathlib.Path(__file__).parent / "fixtures"
def load(n): return json.loads((FIX / n).read_text())

def test_determinism():
    assert scan(load("sample_clean.json")) == scan(load("sample_clean.json"))

def test_clean_when_no_smells():
    out = scan(load("sample_clean.json"))
    assert out["outcome"] == "CLEAN"

def test_flags_smells():
    out = scan(load("sample_smells.json"))
    assert out["outcome"] == "FLAG"
    assert "BARE_EXCEPT" in out["payload"]["findings"]

def test_receipt_stable():
    h = _pipeline_receipt(load("sample_clean.json"))["deterministic_receipt_hash"]
    assert len(h) == 64

if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")): globals()[n](); print("PASS", n)
