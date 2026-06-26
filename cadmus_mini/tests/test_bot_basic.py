import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from cadmus_mini.bot import generate, _pipeline_receipt
from cadmus_mini.gate import REFUSED
FIX = pathlib.Path(__file__).parent / "fixtures"
def load(n): return json.loads((FIX / n).read_text())

def test_determinism():
    assert generate(load("sample_intent.json")) == generate(load("sample_intent.json"))

def test_emits_spec():
    out = generate(load("sample_intent.json"))
    assert out["outcome"] == "EMIT_SPEC" and out["payload"]["spec"]["title"]

def test_incomplete_refused():
    out = generate(load("sample_incomplete.json"))
    assert out["verdict"] == REFUSED

def test_receipt_stable():
    h = _pipeline_receipt(load("sample_intent.json"))["deterministic_receipt_hash"]
    assert len(h) == 64

if __name__ == "__main__":
    for n in sorted(x for x in dir() if x.startswith("test_")): globals()[n](); print("PASS", n)
