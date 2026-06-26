#!/usr/bin/env python3
"""Generate remaining baby-chamber packages."""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LICENSE = (ROOT / "LICENSE").read_text()


def w(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"))


def pkg_files(name: str, title: str, entry: str, modules: dict[str, str], readme: str,
              test_py: str, fixtures: dict[str, str]) -> None:
    base = ROOT / name
    for mod, src in modules.items():
        w(base / name / f"{mod}.py", src)
    w(base / name / "__init__.py", modules["__init__"])
    w(base / "README.md", readme)
    w(base / "LICENSE", LICENSE)
    for fn, content in fixtures.items():
        w(base / "tests" / "fixtures" / fn, content)
    w(base / "tests" / "test_bot_basic.py", test_py)


# --- AURORA ---
aurora_modules = {
"canonical": '''
    """Canonical verdict request — AURORA-mini."""
    from __future__ import annotations

    from dataclasses import dataclass, field


    @dataclass
    class Check:
        name: str
        passed: bool
        detail: str = ""


    @dataclass
    class CanonicalState:
        candidate_id: str
        checks: list[Check]
        raw: dict


    def canonicalize(raw_request: dict) -> CanonicalState:
        raw = raw_request if isinstance(raw_request, dict) else {}
        cid = str(raw.get("candidate_id", raw.get("id", "candidate")))
        checks_raw = raw.get("checks", [])
        checks: list[Check] = []
        if isinstance(checks_raw, list):
            for c in checks_raw:
                if not isinstance(c, dict):
                    continue
                checks.append(Check(
                    name=str(c.get("name", "")),
                    passed=bool(c.get("passed", False)),
                    detail=str(c.get("detail", "")),
                ))
        checks.sort(key=lambda x: x.name)
        return CanonicalState(candidate_id=cid, checks=checks, raw=raw)
''',
"facts": '''
    """Derive check facts — AURORA-mini."""
    from __future__ import annotations

    from .canonical import CanonicalState

    CONFIG = {"min_checks": 1}


    def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
        f: set[str] = set()
        if not state.checks:
            f.add("NO_CHECKS")
        else:
            f.add("HAS_CHECKS")
        failed = [c.name for c in state.checks if not c.passed]
        if failed:
            f.add("HAS_FAILURES")
            f.add(f"FAIL_COUNT_{len(failed)}")
        else:
            f.add("ALL_PASSED")
        if len(state.checks) >= config["min_checks"]:
            f.add("MIN_CHECKS_MET")
        return frozenset(f)
''',
"scoring": '''
    """Score check results — AURORA-mini."""
    from __future__ import annotations

    from .canonical import CanonicalState


    def score_world(state: CanonicalState, facts) -> dict:
        failed = [c.name for c in state.checks if not c.passed]
        passed = [c.name for c in state.checks if c.passed]
        return {
            "passed_checks": passed,
            "failed_checks": failed,
            "pass_count": len(passed),
            "fail_count": len(failed),
        }
''',
"policy": '''
    """Select RELEASE or REFUSE — AURORA-mini."""
    from __future__ import annotations

    from dataclasses import dataclass, field

    from .canonical import CanonicalState


    @dataclass
    class VerdictDecision:
        outcome: str
        payload: dict = field(default_factory=dict)
        reason: str = ""


    def select_action(state: CanonicalState, facts, scores) -> VerdictDecision:
        if "NO_CHECKS" in facts:
            return VerdictDecision("REFUSE", {"reasons": ["no checks provided"]}, "missing checks")
        if "HAS_FAILURES" in facts:
            return VerdictDecision(
                "RELEASE",
                {"candidate_id": state.candidate_id},
                "attempt release despite failures (will be gated)",
            )
        return VerdictDecision(
            "RELEASE",
            {"candidate_id": state.candidate_id, "passed": scores.get("passed_checks", [])},
            "all checks passed",
        )
''',
"gate": '''
    """Verdict gate — release or refuse-with-fallback."""
    from __future__ import annotations

    from dataclasses import dataclass

    from .canonical import CanonicalState
    from .policy import VerdictDecision

    RELEASED = "RELEASED"
    REFUSED = "REFUSED_WITH_FALLBACK"


    @dataclass
    class FinalDecision:
        outcome: str
        payload: dict
        reason: str
        verdict: str = RELEASED
        refusal_reason: str = ""
        candidate_outcome: str = ""

        def to_response(self) -> dict:
            return {
                "outcome": self.outcome,
                "payload": self.payload,
                "reason": self.reason,
                "verdict": self.verdict,
            }


    def _fallback(state: CanonicalState, facts, why: str) -> FinalDecision:
        reasons = [c.name for c in state.checks if not c.passed] or ["no_checks"]
        return FinalDecision("REFUSE", {"reasons": reasons}, "fallback after refusal", REFUSED, why)


    def gate(candidate: VerdictDecision, state: CanonicalState, facts) -> FinalDecision:
        why = ""
        if candidate.outcome == "RELEASE" and "HAS_FAILURES" in facts:
            why = "RELEASE blocked: check failures present"
        elif candidate.outcome == "RELEASE" and "NO_CHECKS" in facts:
            why = "RELEASE blocked: no checks"

        if not why:
            return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
        fb = _fallback(state, facts, why)
        fb.candidate_outcome = candidate.outcome
        return fb
''',
"receipts": '''
    """Deterministic receipts — AURORA-mini."""
    from __future__ import annotations

    import hashlib
    import json


    def make_receipt(state, facts, scores, candidate, final) -> dict:
        core = {
            "candidate_id": state.candidate_id,
            "facts": sorted(facts),
            "pass_count": scores.get("pass_count", 0),
            "fail_count": scores.get("fail_count", 0),
            "candidate_outcome": candidate.outcome,
            "final_outcome": final.outcome,
            "verdict": final.verdict,
            "refusal_reason": final.refusal_reason or None,
        }
        digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {**core, "deterministic_receipt_hash": digest}
''',
"bot": '''
    """AURORA-mini: verdict gate — RELEASE / REFUSE with receipt."""
    from __future__ import annotations

    import json

    from .canonical import canonicalize
    from .facts import derive_facts
    from .gate import gate
    from .policy import select_action
    from .receipts import make_receipt
    from .scoring import score_world


    def _pipeline_receipt(raw_request: dict) -> dict:
        state = canonicalize(raw_request)
        facts = derive_facts(state)
        scores = score_world(state, facts)
        candidate = select_action(state, facts, scores)
        final = gate(candidate, state, facts)
        return make_receipt(state, facts, scores, candidate, final)


    def verdict(raw_request: dict) -> dict:
        receipt = _pipeline_receipt(raw_request)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        state = canonicalize(raw_request)
        facts = derive_facts(state)
        scores = score_world(state, facts)
        candidate = select_action(state, facts, scores)
        final = gate(candidate, state, facts)
        return final.to_response()
''',
"__init__": '''
    """AURORA-mini — verdict gate pattern extraction."""
    from .bot import verdict
    from .canonical import CanonicalState, Check, canonicalize
    from .facts import CONFIG, derive_facts
    from .gate import REFUSED, RELEASED, FinalDecision, gate
    from .policy import VerdictDecision, select_action
    from .receipts import make_receipt
    from .scoring import score_world

    __all__ = [
        "verdict", "canonicalize", "CanonicalState", "Check",
        "derive_facts", "CONFIG", "score_world", "select_action", "VerdictDecision",
        "gate", "FinalDecision", "RELEASED", "REFUSED", "make_receipt",
    ]
    __version__ = "0.1.0"
''',
}

aurora_readme = """# AURORA-mini

Pattern extraction of AURORA — **not** production AURORA. Contains none of its internals.

Runs checks on a candidate → `RELEASE` or `REFUSE` with reasons + deterministic receipt.

```bash
cd aurora_mini && PYTHONPATH=. python3 tests/test_bot_basic.py
```
"""

aurora_test = '''
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
'''

aurora_fixtures = {
    "sample_all_pass.json": """{
  "candidate_id": "cand_001",
  "checks": [
    {"name": "schema_valid", "passed": true},
    {"name": "provenance_present", "passed": true}
  ]
}""",
    "sample_with_failure.json": """{
  "candidate_id": "cand_002",
  "checks": [
    {"name": "schema_valid", "passed": true},
    {"name": "provenance_present", "passed": false, "detail": "missing source"}
  ]
}""",
}

pkg_files("aurora_mini", "AURORA", "verdict", aurora_modules, aurora_readme, aurora_test, aurora_fixtures)
print("aurora_mini OK")

# Continue with more packages in same file - luna, gavel, cipher, vantage, cadmus, bifrost, cosmic, constellation, keystone
# I'll add them in the next write due to length