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
