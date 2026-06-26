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
