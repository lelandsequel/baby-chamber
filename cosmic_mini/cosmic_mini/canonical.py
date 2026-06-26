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
