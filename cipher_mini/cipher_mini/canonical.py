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
