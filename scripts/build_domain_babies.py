#!/usr/bin/env python3
"""Build luna, gavel, cipher, vantage, cadmus, bifrost mini packages."""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LICENSE = (ROOT / "LICENSE").read_text()


def w(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"))


def write_pkg(pkg: str, modules: dict, readme: str, test_py: str, fixtures: dict) -> None:
    base = ROOT / pkg
    for mod, src in modules.items():
        if mod == "__init__":
            w(base / pkg / "__init__.py", src)
        else:
            w(base / pkg / f"{mod}.py", src)
    w(base / "README.md", readme)
    w(base / "LICENSE", LICENSE)
    w(base / "tests" / "test_bot_basic.py", test_py)
    for fn, body in fixtures.items():
        w(base / "tests" / "fixtures" / fn, body)


# ========== LUNA ==========
write_pkg("luna_mini", {
"canonical": '''
    """Canonical hash-chain — LUNA-mini."""
    from __future__ import annotations
    from dataclasses import dataclass, field

    @dataclass
    class ChainEntry:
        index: int
        prev_hash: str
        payload: dict
        entry_hash: str
        raw: dict = field(default_factory=dict)

    @dataclass
    class CanonicalState:
        chain_id: str
        entries: list[ChainEntry]
        raw: dict

    def canonicalize(raw_request: dict) -> CanonicalState:
        raw = raw_request if isinstance(raw_request, dict) else {}
        cid = str(raw.get("chain_id", raw.get("id", "chain")))
        items = raw.get("entries", [])
        entries: list[ChainEntry] = []
        if isinstance(items, list):
            for i, e in enumerate(items):
                if not isinstance(e, dict):
                    continue
                entries.append(ChainEntry(
                    index=int(e.get("index", i)),
                    prev_hash=str(e.get("prev_hash", "")),
                    payload=e.get("payload", {}) if isinstance(e.get("payload"), dict) else {},
                    entry_hash=str(e.get("entry_hash", "")),
                    raw=e,
                ))
        entries.sort(key=lambda x: x.index)
        return CanonicalState(chain_id=cid, entries=entries, raw=raw)
''',
"facts": '''
    """Verify chain links — LUNA-mini."""
    from __future__ import annotations
    import hashlib, json
    from .canonical import CanonicalState

    CONFIG = {"genesis_prev": "0" * 64}

    def _entry_hash(prev: str, payload: dict) -> str:
        core = {"prev_hash": prev, "payload": payload}
        return hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
        f: set[str] = set()
        if not state.entries:
            f.add("EMPTY_CHAIN")
            return frozenset(f)
        f.add("HAS_ENTRIES")
        prev = config["genesis_prev"]
        for e in state.entries:
            if e.prev_hash != prev:
                f.add(f"BROKEN_LINK_AT_{e.index}")
                break
            expected = _entry_hash(prev, e.payload)
            if e.entry_hash != expected:
                f.add(f"HASH_MISMATCH_AT_{e.index}")
                break
            prev = e.entry_hash
        else:
            f.add("CHAIN_INTACT")
        return frozenset(f)
''',
"scoring": '''
    """Score chain integrity — LUNA-mini."""
    from __future__ import annotations
    from .canonical import CanonicalState

    def score_world(state: CanonicalState, facts) -> dict:
        broken = [x for x in facts if x.startswith("BROKEN_LINK") or x.startswith("HASH_MISMATCH")]
        return {"entry_count": len(state.entries), "broken_links": broken, "intact": "CHAIN_INTACT" in facts}
''',
"policy": '''
    """Decide witness outcome — LUNA-mini."""
    from __future__ import annotations
    from dataclasses import dataclass, field
    from .canonical import CanonicalState

    @dataclass
    class WitnessDecision:
        outcome: str
        payload: dict = field(default_factory=dict)
        reason: str = ""

    def select_action(state: CanonicalState, facts, scores) -> WitnessDecision:
        if "EMPTY_CHAIN" in facts:
            return WitnessDecision("REFUSE", {"reason": "empty chain"}, "no entries")
        if "CHAIN_INTACT" in facts:
            return WitnessDecision("VERIFY", {"chain_id": state.chain_id, "length": len(state.entries)}, "chain intact")
        return WitnessDecision("VERIFY", {"chain_id": state.chain_id}, "attempt verify broken chain")
''',
"gate": '''
    """Gate broken chains — LUNA-mini."""
    from __future__ import annotations
    from dataclasses import dataclass
    from .canonical import CanonicalState
    from .policy import WitnessDecision

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
            return {"outcome": self.outcome, "payload": self.payload, "reason": self.reason, "verdict": self.verdict}

    def gate(candidate: WitnessDecision, state: CanonicalState, facts) -> FinalDecision:
        why = ""
        if candidate.outcome == "VERIFY" and "CHAIN_INTACT" not in facts:
            why = "chain link or hash mismatch detected"
        if not why:
            return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
        fb = FinalDecision("REFUSE", {"broken": [x for x in facts if "BROKEN" in x or "MISMATCH" in x]}, "fallback", REFUSED, why)
        fb.candidate_outcome = candidate.outcome
        return fb
''',
"receipts": '''
    """Receipts — LUNA-mini."""
    from __future__ import annotations
    import hashlib, json

    def make_receipt(state, facts, scores, candidate, final) -> dict:
        core = {
            "chain_id": state.chain_id,
            "facts": sorted(facts),
            "entry_count": scores.get("entry_count", 0),
            "candidate_outcome": candidate.outcome,
            "final_outcome": final.outcome,
            "verdict": final.verdict,
            "refusal_reason": final.refusal_reason or None,
        }
        digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {**core, "deterministic_receipt_hash": digest}
''',
"bot": '''
    """LUNA-mini: append-only hash-chain witness."""
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

    def witness(raw_request: dict) -> dict:
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
    from .bot import witness, _pipeline_receipt
    from .canonical import canonicalize, CanonicalState, ChainEntry
    from .facts import derive_facts, CONFIG
    from .gate import gate, FinalDecision, RELEASED, REFUSED
    from .policy import select_action, WitnessDecision
    from .receipts import make_receipt
    from .scoring import score_world
    __version__ = "0.1.0"
''',
}, """# LUNA-mini\n\nPattern extraction — **not** production LUNA. Append-only hash-chain witness.\n\n```bash\ncd luna_mini && PYTHONPATH=. python3 tests/test_bot_basic.py\n```\n""",
'''
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
''',
{
"sample_intact.json": "",  # filled below after hash compute
"sample_broken.json": """{"chain_id":"c2","entries":[{"index":0,"prev_hash":"0000000000000000000000000000000000000000000000000000000000000000","payload":{"evt":"start"},"entry_hash":"deadbeef"}]}""",
})

# Compute intact chain hashes
import hashlib, json
GENESIS = "0" * 64
def eh(prev, payload):
    return hashlib.sha256(json.dumps({"prev_hash": prev, "payload": payload}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
h0 = eh(GENESIS, {"evt": "start"})
h1 = eh(h0, {"evt": "tick", "n": 1})
intact = {"chain_id": "c1", "entries": [
    {"index": 0, "prev_hash": GENESIS, "payload": {"evt": "start"}, "entry_hash": h0},
    {"index": 1, "prev_hash": h0, "payload": {"evt": "tick", "n": 1}, "entry_hash": h1},
]}
w(ROOT / "luna_mini/tests/fixtures/sample_intact.json", json.dumps(intact, indent=2))
print("luna_mini OK")

# ========== GAVEL ==========
write_pkg("gavel_mini", {
"canonical": '''
    """Canonical citation claim — GAVEL-mini."""
    from __future__ import annotations
    from dataclasses import dataclass

    @dataclass
    class CanonicalState:
        claim_id: str
        quote: str
        source_id: str
        raw: dict

    def canonicalize(raw_request: dict) -> CanonicalState:
        raw = raw_request if isinstance(raw_request, dict) else {}
        return CanonicalState(
            claim_id=str(raw.get("claim_id", raw.get("id", "claim"))),
            quote=str(raw.get("quote", "")).strip(),
            source_id=str(raw.get("source_id", raw.get("source", ""))).strip(),
            raw=raw,
        )
''',
"facts": '''
    """Synthetic citation store — GAVEL-mini."""
    from __future__ import annotations
    from .canonical import CanonicalState

    CONFIG = {}
    CITATION_STORE = {
        "syn_case_001": "The court held that synthetic precedent applies.",
        "syn_case_002": "Deterministic verification requires exact quote match.",
        "syn_statute_01": "No value shall be emitted without provenance.",
    }

    def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
        f: set[str] = set()
        if not state.source_id:
            f.add("MISSING_SOURCE")
            return frozenset(f)
        if state.source_id not in CITATION_STORE:
            f.add("UNKNOWN_SOURCE")
            return frozenset(f)
        f.add("SOURCE_FOUND")
        if state.quote == CITATION_STORE[state.source_id]:
            f.add("QUOTE_MATCHES")
        else:
            f.add("QUOTE_MISMATCH")
        return frozenset(f)
''',
"scoring": '''
    from __future__ import annotations
    from .canonical import CanonicalState
    from .facts import CITATION_STORE

    def score_world(state: CanonicalState, facts) -> dict:
        expected = CITATION_STORE.get(state.source_id, "")
        return {"source_id": state.source_id, "expected_len": len(expected), "quote_len": len(state.quote)}
''',
"policy": '''
    from __future__ import annotations
    from dataclasses import dataclass, field
    from .canonical import CanonicalState

    @dataclass
    class AdjudicationDecision:
        outcome: str
        payload: dict = field(default_factory=dict)
        reason: str = ""

    def select_action(state: CanonicalState, facts, scores) -> AdjudicationDecision:
        if "QUOTE_MATCHES" in facts:
            return AdjudicationDecision("VERIFIED", {"source_id": state.source_id}, "quote matches store")
        if "QUOTE_MISMATCH" in facts:
            return AdjudicationDecision("VERIFIED", {"source_id": state.source_id}, "attempt verify mismatch")
        return AdjudicationDecision("REFUSED", {"reason": "unsourced"}, "missing or unknown source")
''',
"gate": '''
    from __future__ import annotations
    from dataclasses import dataclass
    from .canonical import CanonicalState
    from .policy import AdjudicationDecision

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
            return {"outcome": self.outcome, "payload": self.payload, "reason": self.reason, "verdict": self.verdict}

    def gate(candidate: AdjudicationDecision, state: CanonicalState, facts) -> FinalDecision:
        why = ""
        if candidate.outcome == "VERIFIED" and "QUOTE_MATCHES" not in facts:
            why = "VERIFIED requires exact quote match"
        if not why:
            return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
        fb = FinalDecision("REFUSED", {"source_id": state.source_id}, "fallback", REFUSED, why)
        fb.candidate_outcome = candidate.outcome
        return fb
''',
"receipts": '''
    import hashlib, json
    def make_receipt(state, facts, scores, candidate, final) -> dict:
        core = {"claim_id": state.claim_id, "facts": sorted(facts), "candidate_outcome": candidate.outcome,
                "final_outcome": final.outcome, "verdict": final.verdict, "refusal_reason": final.refusal_reason or None}
        digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {**core, "deterministic_receipt_hash": digest}
''',
"bot": '''
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

    def adjudicate(raw_request: dict) -> dict:
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
    from .bot import adjudicate, _pipeline_receipt
    __version__ = "0.1.0"
''',
}, "# GAVEL-mini\n\nPattern extraction — citation verify-or-refuse. Synthetic store only.\n",
'''
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
''',
{
"sample_verified.json": '{"claim_id":"g1","source_id":"syn_case_001","quote":"The court held that synthetic precedent applies."}',
"sample_mismatch.json": '{"claim_id":"g2","source_id":"syn_case_001","quote":"Wrong quote entirely."}',
})
print("gavel_mini OK")

# ========== CIPHER ==========
write_pkg("cipher_mini", {
"canonical": '''
    from __future__ import annotations
    from dataclasses import dataclass, field

    @dataclass
    class SourcedInput:
        name: str
        value: float
        source: str

    @dataclass
    class CanonicalState:
        deal_id: str
        inputs: list[SourcedInput]
        missing: list[str]
        raw: dict

    REQUIRED = ("fcf_year1", "fcf_year2", "discount_rate", "terminal_growth")

    def canonicalize(raw_request: dict) -> CanonicalState:
        raw = raw_request if isinstance(raw_request, dict) else {}
        deal_id = str(raw.get("deal_id", "deal"))
        items = raw.get("inputs", {})
        if not isinstance(items, dict):
            items = {}
        inputs: list[SourcedInput] = []
        missing: list[str] = []
        for name in REQUIRED:
            entry = items.get(name, {})
            if not isinstance(entry, dict):
                missing.append(name)
                continue
            src = str(entry.get("source", "")).strip()
            val = entry.get("value")
            try:
                fval = float(val)
            except (TypeError, ValueError):
                missing.append(name)
                continue
            if not src:
                missing.append(name)
                continue
            inputs.append(SourcedInput(name=name, value=fval, source=src))
        inputs.sort(key=lambda x: x.name)
        return CanonicalState(deal_id=deal_id, inputs=inputs, missing=sorted(missing), raw=raw)
''',
"facts": '''
    from __future__ import annotations
    from .canonical import CanonicalState, REQUIRED
    CONFIG = {}

    def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
        f: set[str] = set()
        if state.missing:
            f.add("HAS_MISSING")
            for m in state.missing:
                f.add(f"MISSING_{m}")
        if len(state.inputs) == len(REQUIRED):
            f.add("ALL_SOURCED")
        return frozenset(f)
''',
"scoring": '''
    from __future__ import annotations
    from .canonical import CanonicalState

    def _dcf(inp: dict[str, float]) -> float:
        f1, f2 = inp["fcf_year1"], inp["fcf_year2"]
        r, g = inp["discount_rate"], inp["terminal_growth"]
        pv1 = f1 / (1 + r)
        pv2 = f2 / ((1 + r) ** 2)
        terminal = f2 * (1 + g) / (r - g) if r > g else 0.0
        pv_term = terminal / ((1 + r) ** 2)
        return round(pv1 + pv2 + pv_term, 6)

    def score_world(state: CanonicalState, facts) -> dict:
        if "ALL_SOURCED" not in facts:
            return {"valuation": None, "input_count": len(state.inputs)}
        vals = {i.name: i.value for i in state.inputs}
        return {"valuation": _dcf(vals), "input_count": len(state.inputs)}
''',
"policy": '''
    from __future__ import annotations
    from dataclasses import dataclass, field
    from .canonical import CanonicalState

    @dataclass
    class ValueDecision:
        outcome: str
        payload: dict = field(default_factory=dict)
        reason: str = ""

    def select_action(state: CanonicalState, facts, scores) -> ValueDecision:
        if "ALL_SOURCED" in facts:
            return ValueDecision("VALUE", {"deal_id": state.deal_id, "valuation": scores["valuation"]}, "dcf complete")
        return ValueDecision("VALUE", {"deal_id": state.deal_id, "valuation": 0}, "attempt value with gaps")
''',
"gate": '''
    from __future__ import annotations
    from dataclasses import dataclass
    from .canonical import CanonicalState
    from .policy import ValueDecision

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
            return {"outcome": self.outcome, "payload": self.payload, "reason": self.reason, "verdict": self.verdict}

    def gate(candidate: ValueDecision, state: CanonicalState, facts) -> FinalDecision:
        why = ""
        if candidate.outcome == "VALUE" and "ALL_SOURCED" not in facts:
            why = "DCF refuses missing or unsourced inputs"
        if not why:
            return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
        fb = FinalDecision("REFUSE", {"missing": state.missing}, "fallback", REFUSED, why)
        fb.candidate_outcome = candidate.outcome
        return fb
''',
"receipts": '''
    import hashlib, json
    def make_receipt(state, facts, scores, candidate, final) -> dict:
        core = {"deal_id": state.deal_id, "facts": sorted(facts), "valuation": scores.get("valuation"),
                "candidate_outcome": candidate.outcome, "final_outcome": final.outcome,
                "verdict": final.verdict, "refusal_reason": final.refusal_reason or None}
        digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {**core, "deterministic_receipt_hash": digest}
''',
"bot": '''
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

    def value(raw_request: dict) -> dict:
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
    from .bot import value, _pipeline_receipt
    __version__ = "0.1.0"
''',
}, "# CIPHER-mini\n\nPattern extraction — 5-line DCF refuse-or-verify.\n",
'''
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
''',
{
"sample_complete.json": """{"deal_id":"d1","inputs":{"fcf_year1":{"value":100,"source":"syn_model"},"fcf_year2":{"value":110,"source":"syn_model"},"discount_rate":{"value":0.10,"source":"syn_wacc"},"terminal_growth":{"value":0.02,"source":"syn_assumption"}}}""",
"sample_missing.json": """{"deal_id":"d2","inputs":{"fcf_year1":{"value":100,"source":"syn_model"},"discount_rate":{"value":0.10,"source":"syn_wacc"}}}""",
})
print("cipher_mini OK")

# ========== VANTAGE ==========
write_pkg("vantage_mini", {
"canonical": '''
    from __future__ import annotations
    from dataclasses import dataclass

    @dataclass
    class CanonicalState:
        file_id: str
        source: str
        raw: dict

    def canonicalize(raw_request: dict) -> CanonicalState:
        raw = raw_request if isinstance(raw_request, dict) else {}
        return CanonicalState(
            file_id=str(raw.get("file_id", "file")),
            source=str(raw.get("source", raw.get("code", ""))),
            raw=raw,
        )
''',
"facts": '''
    from __future__ import annotations
    from .canonical import CanonicalState

    CONFIG = {}
    PATTERNS = (
        ("BARE_EXCEPT", "except:"),
        ("EVAL_USAGE", "eval("),
        ("PRINT_DEBUG", "print("),
        ("HARDCODED_SECRET", "password ="),
    )

    def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
        f: set[str] = set()
        src = state.source
        hits = []
        for name, needle in PATTERNS:
            if needle in src:
                hits.append(name)
                f.add(f"SMELL_{name}")
        if hits:
            f.add("HAS_FINDINGS")
        f.add("ALL_PATTERNS_CHECKED")
        f.add(f"PATTERN_COUNT_{len(PATTERNS)}")
        return frozenset(f)
''',
"scoring": '''
    from __future__ import annotations
    from .canonical import CanonicalState
    from .facts import PATTERNS

    def score_world(state: CanonicalState, facts) -> dict:
        findings = sorted(x.replace("SMELL_", "") for x in facts if x.startswith("SMELL_"))
        return {"findings": findings, "patterns_checked": len(PATTERNS), "finding_count": len(findings)}
''',
"policy": '''
    from __future__ import annotations
    from dataclasses import dataclass, field
    from .canonical import CanonicalState

    @dataclass
    class ScanDecision:
        outcome: str
        payload: dict = field(default_factory=dict)
        reason: str = ""

    def select_action(state: CanonicalState, facts, scores) -> ScanDecision:
        if "HAS_FINDINGS" in facts:
            return ScanDecision("FLAG", {"findings": scores["findings"]}, "smells detected")
        return ScanDecision("CLEAN", {}, "no smells in checked patterns")
''',
"gate": '''
    from __future__ import annotations
    from dataclasses import dataclass
    from .canonical import CanonicalState
    from .policy import ScanDecision

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
            return {"outcome": self.outcome, "payload": self.payload, "reason": self.reason, "verdict": self.verdict}

    def gate(candidate: ScanDecision, state: CanonicalState, facts) -> FinalDecision:
        why = ""
        if candidate.outcome == "CLEAN" and "ALL_PATTERNS_CHECKED" not in facts:
            why = "cannot claim CLEAN without checking all patterns"
        if not why:
            return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
        fb = FinalDecision("FLAG", {"findings": ["INCOMPLETE_SCAN"]}, "fallback", REFUSED, why)
        fb.candidate_outcome = candidate.outcome
        return fb
''',
"receipts": '''
    import hashlib, json
    def make_receipt(state, facts, scores, candidate, final) -> dict:
        core = {"file_id": state.file_id, "facts": sorted(facts), "finding_count": scores.get("finding_count", 0),
                "candidate_outcome": candidate.outcome, "final_outcome": final.outcome,
                "verdict": final.verdict, "refusal_reason": final.refusal_reason or None}
        digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {**core, "deterministic_receipt_hash": digest}
''',
"bot": '''
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

    def scan(raw_request: dict) -> dict:
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
    from .bot import scan, _pipeline_receipt
    __version__ = "0.1.0"
''',
}, "# VANTAGE-mini\n\nPattern extraction — deterministic code-smell flagger.\n",
'''
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
''',
{
"sample_clean.json": '{"file_id":"f1","source":"def add(a, b):\\n    return a + b\\n"}',
"sample_smells.json": '{"file_id":"f2","source":"try:\\n    x=1\\nexcept:\\n    pass\\nprint(x)\\n"}',
})
print("vantage_mini OK")

# ========== CADMUS ==========
write_pkg("cadmus_mini", {
"canonical": '''
    from __future__ import annotations
    from dataclasses import dataclass, field

    @dataclass
    class CanonicalState:
        intent_id: str
        title: str
        goals: list[str]
        constraints: list[str]
        raw: dict

    def canonicalize(raw_request: dict) -> CanonicalState:
        raw = raw_request if isinstance(raw_request, dict) else {}
        goals = raw.get("goals", [])
        constraints = raw.get("constraints", [])
        if not isinstance(goals, list): goals = []
        if not isinstance(constraints, list): constraints = []
        return CanonicalState(
            intent_id=str(raw.get("intent_id", "intent")),
            title=str(raw.get("title", "")).strip(),
            goals=sorted(str(g) for g in goals),
            constraints=sorted(str(c) for c in constraints),
            raw=raw,
        )
''',
"facts": '''
    from __future__ import annotations
    from .canonical import CanonicalState
    CONFIG = {"min_goals": 1}

    def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
        f: set[str] = set()
        if not state.title:
            f.add("MISSING_TITLE")
        if len(state.goals) >= config["min_goals"]:
            f.add("GOALS_PRESENT")
        else:
            f.add("GOALS_MISSING")
        if state.constraints:
            f.add("HAS_CONSTRAINTS")
        return frozenset(f)
''',
"scoring": '''
    from __future__ import annotations
    from .canonical import CanonicalState

    def score_world(state: CanonicalState, facts) -> dict:
        sections = []
        if state.title:
            sections.append("title")
        if state.goals:
            sections.append("goals")
        if state.constraints:
            sections.append("constraints")
        return {"section_count": len(sections), "sections": sections}
''',
"policy": '''
    from __future__ import annotations
    from dataclasses import dataclass, field
    from .canonical import CanonicalState

    @dataclass
    class SpecDecision:
        outcome: str
        payload: dict = field(default_factory=dict)
        reason: str = ""

    def _build_spec(state: CanonicalState) -> dict:
        return {
            "intent_id": state.intent_id,
            "title": state.title,
            "goals": state.goals,
            "constraints": state.constraints,
            "sections": ["overview", "goals", "constraints", "acceptance"],
        }

    def select_action(state: CanonicalState, facts, scores) -> SpecDecision:
        if "GOALS_PRESENT" in facts and state.title:
            return SpecDecision("EMIT_SPEC", {"spec": _build_spec(state)}, "intent complete")
        return SpecDecision("EMIT_SPEC", {"spec": {}}, "attempt spec with incomplete intent")
''',
"gate": '''
    from __future__ import annotations
    from dataclasses import dataclass
    from .canonical import CanonicalState
    from .policy import SpecDecision

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
            return {"outcome": self.outcome, "payload": self.payload, "reason": self.reason, "verdict": self.verdict}

    def gate(candidate: SpecDecision, state: CanonicalState, facts) -> FinalDecision:
        why = ""
        if candidate.outcome == "EMIT_SPEC" and ("GOALS_MISSING" in facts or "MISSING_TITLE" in facts):
            why = "spec generation refused: incomplete intent"
        if not why:
            return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
        fb = FinalDecision("REFUSE", {"intent_id": state.intent_id}, "fallback", REFUSED, why)
        fb.candidate_outcome = candidate.outcome
        return fb
''',
"receipts": '''
    import hashlib, json
    def make_receipt(state, facts, scores, candidate, final) -> dict:
        spec = candidate.payload.get("spec", {})
        core = {"intent_id": state.intent_id, "facts": sorted(facts), "section_count": scores.get("section_count", 0),
                "spec_title": spec.get("title"), "candidate_outcome": candidate.outcome,
                "final_outcome": final.outcome, "verdict": final.verdict, "refusal_reason": final.refusal_reason or None}
        digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {**core, "deterministic_receipt_hash": digest}
''',
"bot": '''
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

    def generate(raw_request: dict) -> dict:
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
    from .bot import generate, _pipeline_receipt
    __version__ = "0.1.0"
''',
}, "# CADMUS-mini\n\nPattern extraction — deterministic spec generator.\n",
'''
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
''',
{
"sample_intent.json": '{"intent_id":"i1","title":"Baby Chamber","goals":["deterministic","receipted"],"constraints":["stdlib only"]}',
"sample_incomplete.json": '{"intent_id":"i2","title":"","goals":[]}',
})
print("cadmus_mini OK")

# ========== BIFROST ==========
write_pkg("bifrost_mini", {
"canonical": '''
    from __future__ import annotations
    from dataclasses import dataclass, field

    @dataclass
    class CanonicalState:
        claim_id: str
        claim: dict
        evidence: dict
        raw: dict

    def canonicalize(raw_request: dict) -> CanonicalState:
        raw = raw_request if isinstance(raw_request, dict) else {}
        claim = raw.get("claim", {})
        evidence = raw.get("evidence", {})
        return CanonicalState(
            claim_id=str(raw.get("claim_id", "claim")),
            claim=claim if isinstance(claim, dict) else {},
            evidence=evidence if isinstance(evidence, dict) else {},
            raw=raw,
        )
''',
"facts": '''
    from __future__ import annotations
    from .canonical import CanonicalState
    CONFIG = {}

    def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
        f: set[str] = set()
        if not state.claim:
            f.add("EMPTY_CLAIM")
            return frozenset(f)
        if not state.evidence:
            f.add("EMPTY_EVIDENCE")
            return frozenset(f)
        f.add("HAS_PAIR")
        mismatches = []
        for k, v in sorted(state.claim.items()):
            if k not in state.evidence:
                mismatches.append(k)
            elif state.evidence[k] != v:
                mismatches.append(k)
        if mismatches:
            f.add("HAS_MISMATCHES")
            f.add(f"MISMATCH_COUNT_{len(mismatches)}")
        else:
            f.add("FULL_MATCH")
        return frozenset(f)
''',
"scoring": '''
    from __future__ import annotations
    from .canonical import CanonicalState

    def score_world(state: CanonicalState, facts) -> dict:
        keys = sorted(state.claim.keys())
        matched = sum(1 for k in keys if state.evidence.get(k) == state.claim[k])
        return {"keys_checked": len(keys), "matched": matched, "match_ratio": round(matched / max(len(keys), 1), 6)}
''',
"policy": '''
    from __future__ import annotations
    from dataclasses import dataclass, field
    from .canonical import CanonicalState

    @dataclass
    class VerifyDecision:
        outcome: str
        payload: dict = field(default_factory=dict)
        reason: str = ""

    def select_action(state: CanonicalState, facts, scores) -> VerifyDecision:
        if "FULL_MATCH" in facts:
            return VerifyDecision("CONFIRM", {"claim_id": state.claim_id, "match_ratio": scores["match_ratio"]}, "claim matches evidence")
        if "HAS_MISMATCHES" in facts:
            return VerifyDecision("CONFIRM", {"claim_id": state.claim_id}, "attempt confirm despite mismatch")
        return VerifyDecision("DENY", {"claim_id": state.claim_id}, "missing claim or evidence")
''',
"gate": '''
    from __future__ import annotations
    from dataclasses import dataclass
    from .canonical import CanonicalState
    from .policy import VerifyDecision

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
            return {"outcome": self.outcome, "payload": self.payload, "reason": self.reason, "verdict": self.verdict}

    def gate(candidate: VerifyDecision, state: CanonicalState, facts) -> FinalDecision:
        why = ""
        if candidate.outcome == "CONFIRM" and "FULL_MATCH" not in facts:
            why = "CONFIRM requires full claim-evidence match"
        if not why:
            return FinalDecision(candidate.outcome, candidate.payload, candidate.reason, RELEASED, "", candidate.outcome)
        fb = FinalDecision("DENY", {"claim_id": state.claim_id, "match_ratio": 0}, "fallback", REFUSED, why)
        fb.candidate_outcome = candidate.outcome
        return fb
''',
"receipts": '''
    import hashlib, json
    def make_receipt(state, facts, scores, candidate, final) -> dict:
        core = {"claim_id": state.claim_id, "facts": sorted(facts), "match_ratio": scores.get("match_ratio"),
                "candidate_outcome": candidate.outcome, "final_outcome": final.outcome,
                "verdict": final.verdict, "refusal_reason": final.refusal_reason or None}
        digest = hashlib.sha256(json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return {**core, "deterministic_receipt_hash": digest}
''',
"bot": '''
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

    def verify(raw_request: dict) -> dict:
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
    from .bot import verify, _pipeline_receipt
    __version__ = "0.1.0"
''',
}, "# BIFROST-mini\n\nPattern extraction — claim vs evidence verifier.\n",
'''
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
''',
{
"sample_match.json": '{"claim_id":"b1","claim":{"status":"active","count":3},"evidence":{"status":"active","count":3}}',
"sample_mismatch.json": '{"claim_id":"b2","claim":{"status":"active","count":3},"evidence":{"status":"active","count":5}}',
})
print("bifrost_mini OK")
print("ALL DOMAIN BABIES BUILT")