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
