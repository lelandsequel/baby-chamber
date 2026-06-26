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
