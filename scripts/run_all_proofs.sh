#!/usr/bin/env bash
# Per-baby proof bundle: green tests · determinism · refusal · leak-scan
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PKGS=(
  strata_mini
  vellum_mini
  aurora_mini
  luna_mini
  gavel_mini
  cipher_mini
  vantage_mini
  cadmus_mini
  bifrost_mini
  cosmic_mini
  constellation_mini
  keystone_mini
)

echo "=== TESTS ==="
for pkg in "${PKGS[@]}"; do
  echo -n "$pkg ... "
  (cd "$pkg" && PYTHONPATH=. python3 tests/test_bot_basic.py > /dev/null)
  echo "GREEN"
done

echo ""
echo "=== DETERMINISM PROOFS ==="
python3 - <<'PY'
import importlib, json, pathlib, sys

ROOT = pathlib.Path(".")
cases = {
    "strata_mini": ("strata_mini.bot", "choose_action", "sample_tick_at_asteroid.json"),
    "vellum_mini": ("vellum_mini.bot", "envelope", "sample_sourced.json"),
    "aurora_mini": ("aurora_mini.bot", "verdict", "sample_all_pass.json"),
    "luna_mini": ("luna_mini.bot", "witness", "sample_intact.json"),
    "gavel_mini": ("gavel_mini.bot", "adjudicate", "sample_verified.json"),
    "cipher_mini": ("cipher_mini.bot", "value", "sample_complete.json"),
    "vantage_mini": ("vantage_mini.bot", "scan", "sample_clean.json"),
    "cadmus_mini": ("cadmus_mini.bot", "generate", "sample_intent.json"),
    "bifrost_mini": ("bifrost_mini.bot", "verify", "sample_match.json"),
    "cosmic_mini": ("cosmic_mini.bot", "run", "sample_spine_ok.json"),
    "constellation_mini": ("constellation_mini.bot", "measure", "sample_within_threshold.json"),
    "keystone_mini": ("keystone_mini.bot", "close", "sample_all_valid.json"),
}
for pkg, (mod, fn, fixture) in cases.items():
    sys.path.insert(0, str(ROOT / pkg))
    m = importlib.import_module(mod)
    pipe = importlib.import_module(mod.replace(".bot", ".bot"))
    raw = json.loads((ROOT / pkg / "tests/fixtures" / fixture).read_text())
    h1 = pipe._pipeline_receipt(raw)["deterministic_receipt_hash"]
    h2 = pipe._pipeline_receipt(raw)["deterministic_receipt_hash"]
    assert h1 == h2, pkg
    print(f"DETERMINISM OK  {pkg}  {h1[:16]}...")
    sys.path.pop(0)
PY

echo ""
echo "=== REFUSAL PROOFS ==="
python3 - <<'PY'
import importlib, json, pathlib, sys

ROOT = pathlib.Path(".")
refusals = {
    "strata_mini": None,
    "vellum_mini": ("vellum_mini.bot", "envelope", "sample_unsourced.json"),
    "aurora_mini": ("aurora_mini.bot", "verdict", "sample_with_failure.json"),
    "luna_mini": ("luna_mini.bot", "witness", "sample_broken.json"),
    "gavel_mini": ("gavel_mini.bot", "adjudicate", "sample_mismatch.json"),
    "cipher_mini": ("cipher_mini.bot", "value", "sample_missing.json"),
    "cadmus_mini": ("cadmus_mini.bot", "generate", "sample_incomplete.json"),
    "bifrost_mini": ("bifrost_mini.bot", "verify", "sample_mismatch.json"),
    "cosmic_mini": ("cosmic_mini.bot", "run", "sample_check_fail.json"),
    "constellation_mini": ("constellation_mini.bot", "measure", "sample_exceeds_threshold.json"),
    "keystone_mini": ("keystone_mini.bot", "close", "sample_missing_receipt.json"),
}
for pkg, case in refusals.items():
    sys.path.insert(0, str(ROOT / pkg))
    if case is None:
        if pkg == "strata_mini":
            from strata_mini.canonical import canonicalize
            from strata_mini.facts import derive_facts
            from strata_mini.gate import REFUSED, gate
            from strata_mini.policy import ActionDecision
            raw = json.loads((ROOT / pkg / "tests/fixtures/sample_tick_empty.json").read_text())
            st = canonicalize(raw)
            fin = gate(ActionDecision("MINE", {}, "forced bad", "MINE_LOCAL"), st, derive_facts(st))
            assert fin.verdict == REFUSED
            print("REFUSAL OK      strata_mini")
        sys.path.pop(0)
        continue
    mod, fn, fixture = case
    pipe = importlib.import_module(mod)
    gate_mod = importlib.import_module(mod.replace(".bot", ".gate"))
    raw = json.loads((ROOT / pkg / "tests/fixtures" / fixture).read_text())
    out = getattr(pipe, fn)(raw)
    assert out["verdict"] == gate_mod.REFUSED, (pkg, out)
    print(f"REFUSAL OK      {pkg}")
    sys.path.pop(0)

# vantage: gate refuses false CLEAN only when patterns unchecked — test via gate directly
sys.path.insert(0, str(ROOT / "vantage_mini"))
from vantage_mini.gate import gate, REFUSED
from vantage_mini.policy import ScanDecision
from vantage_mini.canonical import canonicalize
st = canonicalize({"file_id": "x", "source": "x=1"})
fin = gate(ScanDecision("CLEAN", {}, ""), st, frozenset())
assert fin.verdict == REFUSED
print("REFUSAL OK      vantage_mini")
sys.path.pop(0)
PY

echo ""
echo "=== LEAK SCAN ==="
bash scripts/leak_scan.sh

echo ""
echo "=== ALL PROOFS GREEN ==="