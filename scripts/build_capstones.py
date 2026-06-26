#!/usr/bin/env python3
"""Build cosmic_mini, constellation_mini, keystone_mini capstone packages."""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LICENSE = (ROOT / "LICENSE").read_text()


def w(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"))


def pkg_files(name: str, modules: dict[str, str], readme: str, test_py: str, fixtures: dict[str, str]) -> None:
    base = ROOT / name
    for mod, src in modules.items():
        if mod == "__init__":
            w(base / name / "__init__.py", src)
        else:
            w(base / name / f"{mod}.py", src)
    w(base / "README.md", readme)
    w(base / "LICENSE", LICENSE)
    for fn, content in fixtures.items():
        w(base / "tests" / "fixtures" / fn, content)
    w(base / "tests" / "test_bot_basic.py", test_py)


# ---------------------------------------------------------------------------
# COSMIC_MINI
# ---------------------------------------------------------------------------
cosmic_modules = {
"canonical": '''
    """Canonical spine run request — COSMIC-mini."""
    from __future__ import annotations

    import hashlib
    import json
    from dataclasses import dataclass, field


    GENESIS = "0" * 64


    def _sha(value) -> str:
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


    @dataclass
    class ValueField:
        name: str
        value: object
        source: str
        sha: str


    @dataclass
    class Check:
        name: str
        passed: bool
        detail: str = ""


    @dataclass
    class CanonicalState:
        run_id: str
        values: list[ValueField]
        checks: list[Check]
        chain_id: str
        prev_hash: str
        entry_index: int
        generated: bool
        raw: dict = field(default_factory=dict)


    def synthetic_produce(run_id: str) -> dict:
        """Deterministic synthetic producer — no clock, no random."""
        alpha = {"name": "alpha", "value": 42, "source": "synthetic_cosmic_a"}
        alpha["sha"] = _sha(alpha["value"])
        beta = {"name": "beta", "value": "spine_ok", "source": "synthetic_cosmic_b"}
        beta["sha"] = _sha(beta["value"])
        return {
            "run_id": run_id,
            "produce": {"values": [alpha, beta]},
            "checks": [
                {"name": "provenance_present", "passed": True},
                {"name": "schema_valid", "passed": True},
            ],
            "witness": {"chain_id": f"chain_{run_id}", "prev_hash": GENESIS, "entry_index": 0},
        }


    def canonicalize(raw_request: dict) -> CanonicalState:
        raw = raw_request if isinstance(raw_request, dict) else {}
        generated = False
        if raw.get("generate"):
            run_id = str(raw.get("run_id", "run_synth"))
            raw = synthetic_produce(run_id)
            generated = True

        run_id = str(raw.get("run_id", raw.get("id", "run")))
        produce = raw.get("produce", raw.get("record", {}))
        produce = produce if isinstance(produce, dict) else {}
        items = produce.get("values", produce.get("fields", []))
        if not isinstance(items, list):
            items = []

        values: list[ValueField] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", item.get("field", "")))
            value = item.get("value")
            source = str(item.get("source", "")).strip()
            sha = str(item.get("sha", "")).strip()
            if source and sha == _sha(value):
                values.append(ValueField(name=name, value=value, source=source, sha=sha))
        values.sort(key=lambda v: v.name)

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
        checks.sort(key=lambda c: c.name)

        witness = raw.get("witness", {})
        witness = witness if isinstance(witness, dict) else {}
        chain_id = str(witness.get("chain_id", f"chain_{run_id}"))
        prev_hash = str(witness.get("prev_hash", GENESIS))
        entry_index = int(witness.get("entry_index", 0) or 0)

        return CanonicalState(
            run_id=run_id,
            values=values,
            checks=checks,
            chain_id=chain_id,
            prev_hash=prev_hash,
            entry_index=entry_index,
            generated=generated,
            raw=raw,
        )
''',
"facts": '''
    """Derive spine facts — COSMIC-mini."""
    from __future__ import annotations

    from .canonical import CanonicalState

    CONFIG = {"min_values": 1, "min_checks": 1}


    def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
        f: set[str] = set()
        if state.generated:
            f.add("SYNTHETIC_GENERATED")
        if state.values:
            f.add("HAS_VALUES")
        else:
            f.add("NO_VALUES")
        if len(state.values) >= config["min_values"]:
            f.add("MIN_VALUES_MET")
        if state.checks:
            f.add("HAS_CHECKS")
        else:
            f.add("NO_CHECKS")
        failed = [c.name for c in state.checks if not c.passed]
        if failed:
            f.add("HAS_CHECK_FAILURES")
        elif state.checks:
            f.add("ALL_CHECKS_PASS")
        if state.prev_hash:
            f.add("HAS_WITNESS_CHAIN")
        if (
            "MIN_VALUES_MET" in f
            and "ALL_CHECKS_PASS" in f
            and "HAS_WITNESS_CHAIN" in f
        ):
            f.add("SPINE_READY")
        return frozenset(f)
''',
"scoring": '''
    """Score spine stages — COSMIC-mini."""
    from __future__ import annotations

    from .canonical import CanonicalState


    def score_world(state: CanonicalState, facts) -> dict:
        failed = [c.name for c in state.checks if not c.passed]
        return {
            "value_count": len(state.values),
            "check_count": len(state.checks),
            "failed_checks": failed,
            "chain_id": state.chain_id,
            "entry_index": state.entry_index,
        }
''',
"policy": '''
    """Select spine completion — COSMIC-mini."""
    from __future__ import annotations

    from dataclasses import dataclass, field

    from .canonical import CanonicalState


    @dataclass
    class SpineDecision:
        outcome: str
        payload: dict = field(default_factory=dict)
        reason: str = ""


    def select_action(state: CanonicalState, facts, scores) -> SpineDecision:
        if "SPINE_READY" in facts:
            return SpineDecision(
                "SPINE_COMPLETE",
                {"run_id": state.run_id, "stages": ["produce", "vellum", "aurora", "luna"]},
                "all spine preconditions met",
            )
        if "HAS_CHECK_FAILURES" in facts:
            return SpineDecision(
                "SPINE_COMPLETE",
                {"run_id": state.run_id},
                "attempt complete despite check failures (will be gated)",
            )
        if "NO_VALUES" in facts:
            return SpineDecision("SPINE_ABORT", {}, "no producible values")
        return SpineDecision("SPINE_ABORT", {}, "spine preconditions not met")
''',
"gate": '''
    """Spine gate — refuse incomplete spine."""
    from __future__ import annotations

    from dataclasses import dataclass

    from .canonical import CanonicalState
    from .policy import SpineDecision

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
        reasons = []
        if "NO_VALUES" in facts:
            reasons.append("no_values")
        if "HAS_CHECK_FAILURES" in facts:
            reasons.extend(c.name for c in state.checks if not c.passed)
        if not reasons:
            reasons.append("spine_not_ready")
        return FinalDecision(
            "SPINE_REFUSED",
            {"run_id": state.run_id, "reasons": sorted(reasons)},
            "fallback after refusal",
            REFUSED,
            why,
        )


    def gate(candidate: SpineDecision, state: CanonicalState, facts) -> FinalDecision:
        why = ""
        if candidate.outcome == "SPINE_COMPLETE" and "HAS_CHECK_FAILURES" in facts:
            why = "SPINE_COMPLETE blocked: check failures present"
        elif candidate.outcome == "SPINE_COMPLETE" and "SPINE_READY" not in facts:
            why = "SPINE_COMPLETE blocked: spine not ready"
        if not why:
            return FinalDecision(
                candidate.outcome,
                candidate.payload,
                candidate.reason,
                RELEASED,
                "",
                candidate.outcome,
            )
        fb = _fallback(state, facts, why)
        fb.candidate_outcome = candidate.outcome
        return fb
''',
"receipts": '''
    """Deterministic receipts — COSMIC-mini."""
    from __future__ import annotations

    import hashlib
    import json


    def make_receipt(state, facts, scores, candidate, final, spine_trace: dict | None = None) -> dict:
        core = {
            "run_id": state.run_id,
            "facts": sorted(facts),
            "value_count": scores.get("value_count", 0),
            "check_count": scores.get("check_count", 0),
            "candidate_outcome": candidate.outcome,
            "final_outcome": final.outcome,
            "verdict": final.verdict,
            "refusal_reason": final.refusal_reason or None,
            "spine_trace": spine_trace or {},
        }
        digest = hashlib.sha256(
            json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return {**core, "deterministic_receipt_hash": digest}
''',
"bot": '''
    """COSMIC-mini: trust-shell spine — produce → vellum → aurora → luna → receipt."""
    from __future__ import annotations

    import hashlib
    import json

    from .canonical import canonicalize
    from .facts import derive_facts
    from .gate import REFUSED, RELEASED, gate
    from .policy import select_action
    from .receipts import make_receipt
    from .scoring import score_world


    def _receipt_hash(core: dict) -> str:
        return hashlib.sha256(
            json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


    def _stage_vellum(state) -> dict:
        """Inline VELLUM — provenance envelope."""
        envelopes = [
            {"name": v.name, "value": v.value, "source": v.source, "sha": v.sha}
            for v in state.values
        ]
        outcome = "ENVELOPE_EMIT" if envelopes else "REFUSED_UNSOURCED"
        return {
            "stage": "vellum",
            "outcome": outcome,
            "envelope_count": len(envelopes),
            "envelopes": envelopes,
        }


    def _stage_aurora(state, vellum: dict) -> dict:
        """Inline AURORA — verdict gate."""
        failed = [c.name for c in state.checks if not c.passed]
        if vellum["outcome"] != "ENVELOPE_EMIT":
            outcome = "REFUSE"
        elif failed:
            outcome = "REFUSE"
        elif not state.checks:
            outcome = "REFUSE"
        else:
            outcome = "RELEASE"
        return {
            "stage": "aurora",
            "outcome": outcome,
            "failed_checks": failed,
            "envelope_count": vellum.get("envelope_count", 0),
        }


    def _stage_luna(state, aurora: dict) -> dict:
        """Inline LUNA — append-only hash-chain witness."""
        payload = {
            "aurora_outcome": aurora["outcome"],
            "run_id": state.run_id,
            "envelope_count": aurora.get("envelope_count", 0),
        }
        payload_hash = _receipt_hash(payload)
        entry_core = {
            "chain_id": state.chain_id,
            "entry_index": state.entry_index,
            "payload_hash": payload_hash,
            "prev_hash": state.prev_hash,
        }
        entry_hash = _receipt_hash(entry_core)
        return {
            "stage": "luna",
            "outcome": "WITNESSED" if aurora["outcome"] == "RELEASE" else "WITNESS_REFUSED",
            "chain_id": state.chain_id,
            "entry_hash": entry_hash,
            "prev_hash": state.prev_hash,
            "payload_hash": payload_hash,
        }


    def _execute_spine(state) -> dict:
        produce = {"stage": "produce", "outcome": "PRODUCED", "value_count": len(state.values)}
        vellum = _stage_vellum(state)
        aurora = _stage_aurora(state, vellum)
        luna = _stage_luna(state, aurora)
        return {"produce": produce, "vellum": vellum, "aurora": aurora, "luna": luna}


    def _pipeline_receipt(raw_request: dict) -> dict:
        state = canonicalize(raw_request)
        facts = derive_facts(state)
        scores = score_world(state, facts)
        candidate = select_action(state, facts, scores)
        final = gate(candidate, state, facts)
        trace = _execute_spine(state) if final.verdict == RELEASED else {}
        return make_receipt(state, facts, scores, candidate, final, trace)


    def run(raw_request: dict) -> dict:
        receipt = _pipeline_receipt(raw_request)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        state = canonicalize(raw_request)
        facts = derive_facts(state)
        scores = score_world(state, facts)
        candidate = select_action(state, facts, scores)
        final = gate(candidate, state, facts)
        if final.verdict != RELEASED:
            return final.to_response()
        trace = _execute_spine(state)
        return {
            "outcome": final.outcome,
            "payload": {**final.payload, "spine": trace},
            "reason": final.reason,
            "verdict": final.verdict,
        }
''',
"__init__": '''
    """COSMIC-mini — trust-shell spine integration demo."""
    from .bot import run, _pipeline_receipt
    from .canonical import CanonicalState, Check, ValueField, canonicalize, synthetic_produce
    from .facts import CONFIG, derive_facts
    from .gate import REFUSED, RELEASED, FinalDecision, gate
    from .policy import SpineDecision, select_action
    from .receipts import make_receipt
    from .scoring import score_world

    __all__ = [
        "run", "_pipeline_receipt",
        "canonicalize", "CanonicalState", "ValueField", "Check", "synthetic_produce",
        "derive_facts", "CONFIG", "score_world", "select_action", "SpineDecision",
        "gate", "FinalDecision", "RELEASED", "REFUSED", "make_receipt",
    ]
    __version__ = "0.1.0"
''',
}

cosmic_readme = """# COSMIC-mini

Pattern extraction of COSMIC trust-shell integration — **not** production COSMIC.
Contains none of its internals.

Wires the spine end-to-end (standalone, inline — no sibling package imports):

```
produce → VELLUM envelope → AURORA gate → LUNA witness → receipt
```

- **No LLMs at runtime.** Pure deterministic Python (stdlib only in core).
- **Same input + same config ⇒ same facts, same outcome, same receipt hash.**
- Synthetic fixtures only. `generate: true` feeds the synthetic producer.

## Run tests

```bash
cd cosmic_mini
PYTHONPATH=. python3 tests/test_bot_basic.py
```

## Output

`run(raw)` returns the gated spine outcome and prints a deterministic receipt with
`deterministic_receipt_hash` (sha256, sorted keys, no timestamps).

— COSMIC-mini · deterministic, receipted, refusal-first.
"""

cosmic_test = '''
    import json, pathlib, sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from cosmic_mini.bot import _pipeline_receipt, run
    from cosmic_mini.canonical import canonicalize
    from cosmic_mini.facts import derive_facts
    from cosmic_mini.gate import REFUSED, gate
    from cosmic_mini.policy import SpineDecision, select_action
    from cosmic_mini.scoring import score_world
    FIX = pathlib.Path(__file__).parent / "fixtures"

    def load(n):
        return json.loads((FIX / n).read_text())

    def test_determinism():
        assert run(load("sample_spine_ok.json")) == run(load("sample_spine_ok.json"))

    def test_spine_completes():
        out = run(load("sample_spine_ok.json"))
        assert out["outcome"] == "SPINE_COMPLETE"
        assert out["verdict"] == "RELEASED"
        assert "spine" in out["payload"]
        assert out["payload"]["spine"]["luna"]["outcome"] == "WITNESSED"

    def test_synthetic_generator():
        out = run({"generate": True, "run_id": "synth_001"})
        assert out["outcome"] == "SPINE_COMPLETE"
        assert out["payload"]["spine"]["produce"]["value_count"] >= 1

    def test_check_failure_refused():
        st = canonicalize(load("sample_check_fail.json"))
        f = derive_facts(st)
        sc = score_world(st, f)
        c = select_action(st, f, sc)
        fin = gate(c, st, f)
        assert fin.verdict == REFUSED
        assert fin.outcome == "SPINE_REFUSED"

    def test_receipt_stable():
        h1 = _pipeline_receipt(load("sample_spine_ok.json"))["deterministic_receipt_hash"]
        h2 = _pipeline_receipt(load("sample_spine_ok.json"))["deterministic_receipt_hash"]
        assert h1 == h2 and len(h1) == 64

    if __name__ == "__main__":
        for n in sorted(x for x in dir() if x.startswith("test_")):
            globals()[n]()
            print("PASS", n)
'''

cosmic_fixtures = {
    "sample_spine_ok.json": """{
  "run_id": "run_001",
  "produce": {
    "values": [
      {
        "name": "alpha",
        "value": 42,
        "source": "synthetic_cosmic_a",
        "sha": "73475cb40a568e8da8a045ced110137e159f890ac4da883b6b17dc651b3a8049"
      },
      {
        "name": "beta",
        "value": "spine_ok",
        "source": "synthetic_cosmic_b",
        "sha": "c9e62d7fe0b5f8c8b7e2e0e6e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0"
      }
    ]
  },
  "checks": [
    {"name": "provenance_present", "passed": true},
    {"name": "schema_valid", "passed": true}
  ],
  "witness": {"chain_id": "chain_run_001", "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000", "entry_index": 0}
}""",
    "sample_check_fail.json": """{
  "run_id": "run_002",
  "produce": {
    "values": [
      {
        "name": "alpha",
        "value": 42,
        "source": "synthetic_cosmic_a",
        "sha": "73475cb40a568e8da8a045ced110137e159f890ac4da883b6b17dc651b3a8049"
      }
    ]
  },
  "checks": [
    {"name": "schema_valid", "passed": true},
    {"name": "provenance_present", "passed": false, "detail": "missing source on field gamma"}
  ],
  "witness": {"chain_id": "chain_run_002", "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000", "entry_index": 0}
}""",
}

# Fix beta sha in fixture - need correct hash
import hashlib, json as _json
_beta_sha = hashlib.sha256(_json.dumps("spine_ok", sort_keys=True, separators=(",", ":")).encode()).hexdigest()
cosmic_fixtures["sample_spine_ok.json"] = cosmic_fixtures["sample_spine_ok.json"].replace(
    "c9e62d7fe0b5f8c8b7e2e0e6e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0e0",
    _beta_sha,
)

# ---------------------------------------------------------------------------
# CONSTELLATION_MINI
# ---------------------------------------------------------------------------
constellation_modules = {
"canonical": '''
    """Canonical drift measure request — CONSTELLATION-mini."""
    from __future__ import annotations

    import hashlib
    import json
    from dataclasses import dataclass, field


    def _sha(value) -> str:
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


    @dataclass
    class CanonicalState:
        bedrock_id: str
        signer_id: str
        baseline_vector: dict[str, float]
        sample_vector: dict[str, float]
        bedrock_hash: str
        signature: str
        threshold: float
        reanchor_requested: bool
        raw: dict = field(default_factory=dict)


    def _vector(raw: dict) -> dict[str, float]:
        out: dict[str, float] = {}
        if not isinstance(raw, dict):
            return out
        for k, v in raw.items():
            try:
                out[str(k)] = float(v)
            except (TypeError, ValueError):
                continue
        return dict(sorted(out.items()))


    def _bedrock_core(bedrock_id: str, vector: dict[str, float], signer_id: str) -> dict:
        return {"bedrock_id": bedrock_id, "signer_id": signer_id, "vector": vector}


    def canonicalize(raw_request: dict) -> CanonicalState:
        raw = raw_request if isinstance(raw_request, dict) else {}
        baseline = raw.get("baseline", {})
        baseline = baseline if isinstance(baseline, dict) else {}
        sample = raw.get("sample", {})
        sample = sample if isinstance(sample, dict) else {}

        bedrock_id = str(baseline.get("bedrock_id", raw.get("bedrock_id", "bedrock")))
        signer_id = str(baseline.get("signer_id", "synthetic_signer"))
        baseline_vector = _vector(baseline.get("vector", baseline.get("bedrock", {})))
        sample_vector = _vector(sample.get("vector", sample))

        core = _bedrock_core(bedrock_id, baseline_vector, signer_id)
        expected_hash = _sha(core)
        bedrock_hash = str(baseline.get("bedrock_hash", "")).strip()
        signature = str(baseline.get("signature", "")).strip()
        expected_sig = _sha({"bedrock_hash": expected_hash, "signer_id": signer_id})

        threshold = float(raw.get("threshold", baseline.get("threshold", 1.0)) or 1.0)
        reanchor = bool(raw.get("reanchor", raw.get("action") == "reanchor"))

        return CanonicalState(
            bedrock_id=bedrock_id,
            signer_id=signer_id,
            baseline_vector=baseline_vector,
            sample_vector=sample_vector,
            bedrock_hash=bedrock_hash or expected_hash,
            signature=signature or expected_sig,
            threshold=threshold,
            reanchor_requested=reanchor,
            raw=raw,
        )
''',
"facts": '''
    """Derive drift facts — CONSTELLATION-mini."""
    from __future__ import annotations

    from .canonical import CanonicalState


    def derive_facts(state: CanonicalState) -> frozenset[str]:
        f: set[str] = set()
        if state.reanchor_requested:
            f.add("REANCHOR_REQUESTED")
        if state.baseline_vector:
            f.add("HAS_BASELINE")
        else:
            f.add("NO_BASELINE")
        if state.sample_vector:
            f.add("HAS_SAMPLE")
        else:
            f.add("NO_SAMPLE")
        # signed bedrock validity checked in scoring; facts mirror scores
        return frozenset(f)
''',
"scoring": '''
    """Compute drift distance from signed bedrock — CONSTELLATION-mini."""
    from __future__ import annotations

    import hashlib
    import json
    import math

    from .canonical import CanonicalState, _bedrock_core, _sha


    def _distance(baseline: dict[str, float], sample: dict[str, float]) -> float:
        keys = sorted(set(baseline) | set(sample))
        if not keys:
            return 0.0
        total = 0.0
        for k in keys:
            diff = sample.get(k, 0.0) - baseline.get(k, 0.0)
            total += diff * diff
        return round(math.sqrt(total), 6)


    def _bedrock_valid(state: CanonicalState) -> bool:
        core = _bedrock_core(state.bedrock_id, state.baseline_vector, state.signer_id)
        expected_hash = _sha(core)
        expected_sig = _sha({"bedrock_hash": expected_hash, "signer_id": state.signer_id})
        return state.bedrock_hash == expected_hash and state.signature == expected_sig


    def score_world(state: CanonicalState, facts) -> dict:
        distance = _distance(state.baseline_vector, state.sample_vector)
        valid = _bedrock_valid(state)
        exceeds = distance > state.threshold
        return {
            "drift_distance": distance,
            "threshold": state.threshold,
            "bedrock_valid": valid,
            "exceeds_threshold": exceeds,
            "baseline_keys": sorted(state.baseline_vector),
            "sample_keys": sorted(state.sample_vector),
        }
''',
"policy": '''
    """Select drift measure outcome — CONSTELLATION-mini."""
    from __future__ import annotations

    from dataclasses import dataclass, field

    from .canonical import CanonicalState


    @dataclass
    class MeasureDecision:
        outcome: str
        payload: dict = field(default_factory=dict)
        reason: str = ""


    def select_action(state: CanonicalState, facts, scores) -> MeasureDecision:
        if "REANCHOR_REQUESTED" in facts:
            return MeasureDecision(
                "REANCHOR",
                {"bedrock_id": state.bedrock_id},
                "re-anchor to signed bedrock requested (will be gated)",
            )
        if not scores.get("bedrock_valid"):
            return MeasureDecision("MEASURE_REFUSE", {}, "invalid signed bedrock")
        if scores.get("exceeds_threshold"):
            return MeasureDecision(
                "MEASURE_FLAG",
                {
                    "bedrock_id": state.bedrock_id,
                    "drift_distance": scores.get("drift_distance", 0.0),
                },
                "drift exceeds threshold (will be gated)",
            )
        return MeasureDecision(
            "MEASURE_OK",
            {
                "bedrock_id": state.bedrock_id,
                "drift_distance": scores.get("drift_distance", 0.0),
            },
            "drift within threshold",
        )
''',
"gate": '''
    """Drift gate — refuse past threshold; never re-anchor."""
    from __future__ import annotations

    from dataclasses import dataclass

    from .canonical import CanonicalState
    from .policy import MeasureDecision

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


    def _fallback(state: CanonicalState, facts, scores, why: str) -> FinalDecision:
        return FinalDecision(
            "DRIFT_REFUSED",
            {
                "bedrock_id": state.bedrock_id,
                "drift_distance": scores.get("drift_distance", 0.0),
                "threshold": state.threshold,
            },
            "fallback after refusal",
            REFUSED,
            why,
        )


    def gate(candidate: MeasureDecision, state: CanonicalState, facts, scores) -> FinalDecision:
        why = ""
        if candidate.outcome == "REANCHOR":
            why = "REANCHOR blocked: re-anchor to signed bedrock is never permitted"
        elif candidate.outcome == "MEASURE_FLAG":
            why = f"drift {scores.get('drift_distance')} exceeds threshold {state.threshold}"
        elif candidate.outcome == "MEASURE_REFUSE":
            why = "signed bedrock hash or signature invalid"
        elif "NO_BASELINE" in facts or "NO_SAMPLE" in facts:
            why = "measurement requires baseline and sample vectors"

        if not why:
            return FinalDecision(
                candidate.outcome,
                candidate.payload,
                candidate.reason,
                RELEASED,
                "",
                candidate.outcome,
            )
        fb = _fallback(state, facts, scores, why)
        fb.candidate_outcome = candidate.outcome
        return fb
''',
"receipts": '''
    """Deterministic receipts — CONSTELLATION-mini."""
    from __future__ import annotations

    import hashlib
    import json


    def make_receipt(state, facts, scores, candidate, final) -> dict:
        core = {
            "bedrock_id": state.bedrock_id,
            "facts": sorted(facts),
            "drift_distance": scores.get("drift_distance", 0.0),
            "threshold": scores.get("threshold", 0.0),
            "bedrock_valid": scores.get("bedrock_valid", False),
            "candidate_outcome": candidate.outcome,
            "final_outcome": final.outcome,
            "verdict": final.verdict,
            "refusal_reason": final.refusal_reason or None,
        }
        digest = hashlib.sha256(
            json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return {**core, "deterministic_receipt_hash": digest}
''',
"bot": '''
    """CONSTELLATION-mini: drift distance from signed bedrock."""
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
        final = gate(candidate, state, facts, scores)
        return make_receipt(state, facts, scores, candidate, final)


    def measure(raw_request: dict) -> dict:
        receipt = _pipeline_receipt(raw_request)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        state = canonicalize(raw_request)
        facts = derive_facts(state)
        scores = score_world(state, facts)
        candidate = select_action(state, facts, scores)
        final = gate(candidate, state, facts, scores)
        return final.to_response()
''',
"__init__": '''
    """CONSTELLATION-mini — drift distance from signed bedrock."""
    from .bot import measure, _pipeline_receipt
    from .canonical import CanonicalState, canonicalize
    from .facts import derive_facts
    from .gate import REFUSED, RELEASED, FinalDecision, gate
    from .policy import MeasureDecision, select_action
    from .receipts import make_receipt
    from .scoring import score_world

    __all__ = [
        "measure", "_pipeline_receipt",
        "canonicalize", "CanonicalState",
        "derive_facts", "score_world", "select_action", "MeasureDecision",
        "gate", "FinalDecision", "RELEASED", "REFUSED", "make_receipt",
    ]
    __version__ = "0.1.0"
''',
}

# Build constellation fixtures with correct hashes
def _bedrock_fixture(bedrock_id, vector, signer_id="synthetic_signer"):
    core = {"bedrock_id": bedrock_id, "signer_id": signer_id, "vector": dict(sorted(vector.items()))}
    bh = hashlib.sha256(_json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    sig = hashlib.sha256(_json.dumps({"bedrock_hash": bh, "signer_id": signer_id}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return core, bh, sig

_bcore, _bh, _sig = _bedrock_fixture("bed_001", {"alpha": 1.0, "beta": 2.0})

constellation_readme = """# CONSTELLATION-mini

Pattern extraction of CONSTELLATION drift measurement — **not** production CONSTELLATION.
Contains none of its internals.

Given a **signed bedrock baseline** and a **current sample**, computes deterministic
drift distance and refuses when past threshold. **Re-anchor to signed bedrock is never
permitted.**

```
baseline + sample → canonicalize → distance → policy → gate → receipt
```

- **No LLMs at runtime.** Pure deterministic Python (stdlib only in core).
- **Same input + same config ⇒ same distance, same outcome, same receipt hash.**
- Synthetic fixtures only.

## Run tests

```bash
cd constellation_mini
PYTHONPATH=. python3 tests/test_bot_basic.py
```

## Output

`measure(raw)` returns the gated drift outcome and prints a deterministic receipt.

— CONSTELLATION-mini · deterministic, receipted, refusal-first.
"""

constellation_test = '''
    import json, pathlib, sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from constellation_mini.bot import _pipeline_receipt, measure
    from constellation_mini.canonical import canonicalize
    from constellation_mini.facts import derive_facts
    from constellation_mini.gate import REFUSED, gate
    from constellation_mini.policy import MeasureDecision, select_action
    from constellation_mini.scoring import score_world
    FIX = pathlib.Path(__file__).parent / "fixtures"

    def load(n):
        return json.loads((FIX / n).read_text())

    def test_determinism():
        assert measure(load("sample_within_threshold.json")) == measure(load("sample_within_threshold.json"))

    def test_within_threshold_ok():
        out = measure(load("sample_within_threshold.json"))
        assert out["outcome"] == "MEASURE_OK"
        assert out["verdict"] == "RELEASED"

    def test_exceeds_threshold_refused():
        out = measure(load("sample_exceeds_threshold.json"))
        assert out["verdict"] == REFUSED
        assert out["outcome"] == "DRIFT_REFUSED"

    def test_reanchor_always_refused():
        out = measure(load("sample_reanchor_request.json"))
        assert out["verdict"] == REFUSED
        assert "re-anchor" in out["reason"].lower() or out["outcome"] == "DRIFT_REFUSED"

    def test_receipt_stable():
        h1 = _pipeline_receipt(load("sample_within_threshold.json"))["deterministic_receipt_hash"]
        h2 = _pipeline_receipt(load("sample_within_threshold.json"))["deterministic_receipt_hash"]
        assert h1 == h2 and len(h1) == 64

    if __name__ == "__main__":
        for n in sorted(x for x in dir() if x.startswith("test_")):
            globals()[n]()
            print("PASS", n)
'''

constellation_fixtures = {
    "sample_within_threshold.json": _json.dumps({
        "baseline": {
            "bedrock_id": "bed_001",
            "signer_id": "synthetic_signer",
            "vector": {"alpha": 1.0, "beta": 2.0},
            "bedrock_hash": _bh,
            "signature": _sig,
        },
        "sample": {"vector": {"alpha": 1.1, "beta": 2.0}},
        "threshold": 0.5,
    }, indent=2),
    "sample_exceeds_threshold.json": _json.dumps({
        "baseline": {
            "bedrock_id": "bed_001",
            "signer_id": "synthetic_signer",
            "vector": {"alpha": 1.0, "beta": 2.0},
            "bedrock_hash": _bh,
            "signature": _sig,
        },
        "sample": {"vector": {"alpha": 5.0, "beta": 2.0}},
        "threshold": 0.5,
    }, indent=2),
    "sample_reanchor_request.json": _json.dumps({
        "baseline": {
            "bedrock_id": "bed_001",
            "signer_id": "synthetic_signer",
            "vector": {"alpha": 1.0, "beta": 2.0},
            "bedrock_hash": _bh,
            "signature": _sig,
        },
        "sample": {"vector": {"alpha": 1.0, "beta": 2.0}},
        "reanchor": True,
        "threshold": 1.0,
    }, indent=2),
}

# ---------------------------------------------------------------------------
# KEYSTONE_MINI
# ---------------------------------------------------------------------------
keystone_modules = {
"canonical": '''
    """Canonical close request — KEYSTONE-mini."""
    from __future__ import annotations

    from dataclasses import dataclass, field


    @dataclass
    class CanonicalState:
        close_id: str
        required_stages: list[str]
        upstream_receipts: dict[str, dict]
        raw: dict = field(default_factory=dict)


    def canonicalize(raw_request: dict) -> CanonicalState:
        raw = raw_request if isinstance(raw_request, dict) else {}
        close_id = str(raw.get("close_id", raw.get("id", "close")))
        required = raw.get("required_stages", ["vellum", "aurora", "luna"])
        if not isinstance(required, list):
            required = ["vellum", "aurora", "luna"]
        required = sorted(str(s) for s in required)

        receipts_raw = raw.get("upstream_receipts", raw.get("receipts", {}))
        receipts: dict[str, dict] = {}
        if isinstance(receipts_raw, dict):
            for k, v in receipts_raw.items():
                if isinstance(v, dict):
                    receipts[str(k)] = v

        return CanonicalState(
            close_id=close_id,
            required_stages=required,
            upstream_receipts=receipts,
            raw=raw,
        )
''',
"facts": '''
    """Derive integrity facts — KEYSTONE-mini."""
    from __future__ import annotations

    from .canonical import CanonicalState


    def derive_facts(state: CanonicalState) -> frozenset[str]:
        f: set[str] = set()
        present = set(state.upstream_receipts)
        required = set(state.required_stages)
        missing = sorted(required - present)
        if missing:
            f.add("MISSING_RECEIPTS")
            f.add(f"MISSING_COUNT_{len(missing)}")
        else:
            f.add("ALL_RECEIPTS_PRESENT")
        if present:
            f.add("HAS_ANY_RECEIPT")
        return frozenset(f)
''',
"scoring": '''
    """Verify upstream receipt hashes — KEYSTONE-mini."""
    from __future__ import annotations

    import hashlib
    import json

    from .canonical import CanonicalState


    def _recompute_hash(receipt: dict) -> str:
        core = {k: v for k, v in receipt.items() if k != "deterministic_receipt_hash"}
        return hashlib.sha256(
            json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


    def verify_receipt(receipt: dict) -> bool:
        if not isinstance(receipt, dict):
            return False
        expected = receipt.get("deterministic_receipt_hash", "")
        if not expected or len(expected) != 64:
            return False
        return _recompute_hash(receipt) == expected


    def score_world(state: CanonicalState, facts) -> dict:
        valid: list[str] = []
        invalid: list[str] = []
        missing = sorted(set(state.required_stages) - set(state.upstream_receipts))
        for stage in state.required_stages:
            rec = state.upstream_receipts.get(stage)
            if rec is None:
                continue
            if verify_receipt(rec):
                valid.append(stage)
            else:
                invalid.append(stage)
        return {
            "valid_stages": sorted(valid),
            "invalid_stages": sorted(invalid),
            "missing_stages": missing,
            "all_valid": not missing and not invalid and len(valid) == len(state.required_stages),
        }
''',
"policy": '''
    """Select CLOSE outcome — KEYSTONE-mini."""
    from __future__ import annotations

    from dataclasses import dataclass, field

    from .canonical import CanonicalState


    @dataclass
    class CloseDecision:
        outcome: str
        payload: dict = field(default_factory=dict)
        reason: str = ""


    def select_action(state: CanonicalState, facts, scores) -> CloseDecision:
        if scores.get("all_valid"):
            return CloseDecision(
                "CLOSE",
                {"close_id": state.close_id, "locked_stages": scores.get("valid_stages", [])},
                "all upstream receipts present and hash-valid",
            )
        if scores.get("missing_stages"):
            return CloseDecision(
                "CLOSE",
                {"close_id": state.close_id},
                "attempt close despite missing receipts (will be gated)",
            )
        return CloseDecision(
            "CLOSE",
            {"close_id": state.close_id},
            "attempt close despite invalid receipt hashes (will be gated)",
        )
''',
"gate": '''
    """Integrity gate — refuse CLOSE unless all receipts valid."""
    from __future__ import annotations

    from dataclasses import dataclass

    from .canonical import CanonicalState
    from .policy import CloseDecision

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


    def _fallback(state: CanonicalState, scores, why: str) -> FinalDecision:
        return FinalDecision(
            "CLOSE_REFUSED",
            {
                "close_id": state.close_id,
                "missing_stages": scores.get("missing_stages", []),
                "invalid_stages": scores.get("invalid_stages", []),
            },
            "fallback after refusal",
            REFUSED,
            why,
        )


    def gate(candidate: CloseDecision, state: CanonicalState, facts, scores) -> FinalDecision:
        why = ""
        if candidate.outcome == "CLOSE" and not scores.get("all_valid"):
            missing = scores.get("missing_stages", [])
            invalid = scores.get("invalid_stages", [])
            if missing:
                why = f"CLOSE blocked: missing upstream receipts for {missing}"
            elif invalid:
                why = f"CLOSE blocked: invalid receipt hash for {invalid}"
            else:
                why = "CLOSE blocked: upstream integrity check failed"
        if not why:
            return FinalDecision(
                candidate.outcome,
                candidate.payload,
                candidate.reason,
                RELEASED,
                "",
                candidate.outcome,
            )
        fb = _fallback(state, scores, why)
        fb.candidate_outcome = candidate.outcome
        return fb
''',
"receipts": '''
    """Deterministic receipts — KEYSTONE-mini."""
    from __future__ import annotations

    import hashlib
    import json


    def make_receipt(state, facts, scores, candidate, final) -> dict:
        core = {
            "close_id": state.close_id,
            "facts": sorted(facts),
            "required_stages": state.required_stages,
            "valid_stages": scores.get("valid_stages", []),
            "invalid_stages": scores.get("invalid_stages", []),
            "missing_stages": scores.get("missing_stages", []),
            "candidate_outcome": candidate.outcome,
            "final_outcome": final.outcome,
            "verdict": final.verdict,
            "refusal_reason": final.refusal_reason or None,
        }
        digest = hashlib.sha256(
            json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return {**core, "deterministic_receipt_hash": digest}
''',
"bot": '''
    """KEYSTONE-mini: upstream receipt integrity lock."""
    from __future__ import annotations

    import json

    from .canonical import canonicalize
    from .facts import derive_facts
    from .gate import gate
    from .policy import select_action
    from .receipts import make_receipt
    from .scoring import score_world, verify_receipt


    def _pipeline_receipt(raw_request: dict) -> dict:
        state = canonicalize(raw_request)
        facts = derive_facts(state)
        scores = score_world(state, facts)
        candidate = select_action(state, facts, scores)
        final = gate(candidate, state, facts, scores)
        return make_receipt(state, facts, scores, candidate, final)


    def close(raw_request: dict) -> dict:
        receipt = _pipeline_receipt(raw_request)
        print(json.dumps(receipt, indent=2, sort_keys=True))
        state = canonicalize(raw_request)
        facts = derive_facts(state)
        scores = score_world(state, facts)
        candidate = select_action(state, facts, scores)
        final = gate(candidate, state, facts, scores)
        return final.to_response()
''',
"__init__": '''
    """KEYSTONE-mini — upstream receipt integrity lock."""
    from .bot import close, _pipeline_receipt
    from .canonical import CanonicalState, canonicalize
    from .facts import derive_facts
    from .gate import REFUSED, RELEASED, FinalDecision, gate
    from .policy import CloseDecision, select_action
    from .receipts import make_receipt
    from .scoring import score_world, verify_receipt

    __all__ = [
        "close", "_pipeline_receipt",
        "canonicalize", "CanonicalState",
        "derive_facts", "score_world", "verify_receipt",
        "select_action", "CloseDecision",
        "gate", "FinalDecision", "RELEASED", "REFUSED", "make_receipt",
    ]
    __version__ = "0.1.0"
''',
}


def _upstream_receipt(stage: str, record_id: str, outcome: str, extra: dict | None = None) -> dict:
    core = {
        "stage": stage,
        "record_id": record_id,
        "final_outcome": outcome,
        "verdict": "RELEASED",
        "refusal_reason": None,
    }
    if extra:
        core.update(extra)
    digest = hashlib.sha256(_json.dumps(core, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {**core, "deterministic_receipt_hash": digest}


_vellum = _upstream_receipt("vellum", "rec_close_001", "ENVELOPE_EMIT", {"envelope_count": 2})
_aurora = _upstream_receipt("aurora", "rec_close_001", "RELEASE", {"pass_count": 2})
_luna = _upstream_receipt("luna", "rec_close_001", "WITNESSED", {"entry_index": 0})
_bad = {**_vellum, "deterministic_receipt_hash": "f" * 64}

keystone_readme = """# KEYSTONE-mini

Pattern extraction of KEYSTONE load-bearing integrity — **not** production KEYSTONE.
Contains none of its internals.

Refuses to **CLOSE** unless every required upstream receipt is present and its
`deterministic_receipt_hash` is recomputable from core fields.

```
upstream receipts → verify hashes → policy → gate → receipt
```

- **No LLMs at runtime.** Pure deterministic Python (stdlib only in core).
- **Same input + same config ⇒ same outcome, same receipt hash.**
- Synthetic fixtures only.

## Run tests

```bash
cd keystone_mini
PYTHONPATH=. python3 tests/test_bot_basic.py
```

## Output

`close(raw)` returns the gated close outcome and prints a deterministic receipt.

— KEYSTONE-mini · deterministic, receipted, refusal-first.
"""

keystone_test = '''
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
'''

keystone_fixtures = {
    "sample_all_valid.json": _json.dumps({
        "close_id": "close_001",
        "required_stages": ["vellum", "aurora", "luna"],
        "upstream_receipts": {"vellum": _vellum, "aurora": _aurora, "luna": _luna},
    }, indent=2),
    "sample_missing_receipt.json": _json.dumps({
        "close_id": "close_002",
        "required_stages": ["vellum", "aurora", "luna"],
        "upstream_receipts": {"vellum": _vellum, "aurora": _aurora},
    }, indent=2),
    "sample_invalid_hash.json": _json.dumps({
        "close_id": "close_003",
        "required_stages": ["vellum", "aurora", "luna"],
        "upstream_receipts": {"vellum": _bad, "aurora": _aurora, "luna": _luna},
    }, indent=2),
}


if __name__ == "__main__":
    pkg_files("cosmic_mini", cosmic_modules, cosmic_readme, cosmic_test, cosmic_fixtures)
    print("cosmic_mini OK")
    pkg_files("constellation_mini", constellation_modules, constellation_readme, constellation_test, constellation_fixtures)
    print("constellation_mini OK")
    pkg_files("keystone_mini", keystone_modules, keystone_readme, keystone_test, keystone_fixtures)
    print("keystone_mini OK")