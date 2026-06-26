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
