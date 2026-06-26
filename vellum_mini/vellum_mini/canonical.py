"""Canonical provenance request — VELLUM-mini."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


def _content_sha(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


@dataclass
class ValueField:
    name: str
    value: object
    source: str
    sha: str
    raw: dict = field(default_factory=dict)


@dataclass
class CanonicalState:
    record_id: str
    fields: list[ValueField]
    unsourced_fields: list[str]
    raw: dict


def canonicalize(raw_request: dict) -> CanonicalState:
    raw = raw_request if isinstance(raw_request, dict) else {}
    record_id = str(raw.get("record_id", raw.get("id", "record")))
    items = raw.get("values", raw.get("fields", []))
    if not isinstance(items, list):
        items = []

    fields: list[ValueField] = []
    unsourced: list[str] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", item.get("field", "")))
        value = item.get("value")
        source = str(item.get("source", "")).strip()
        sha = str(item.get("sha", "")).strip()
        if not source or not sha:
            unsourced.append(name or "unknown")
            continue
        expected = _content_sha(value)
        if sha != expected:
            unsourced.append(name or "unknown")
            continue
        fields.append(ValueField(name=name, value=value, source=source, sha=sha, raw=item))

    fields.sort(key=lambda f: f.name)
    return CanonicalState(
        record_id=record_id,
        fields=fields,
        unsourced_fields=sorted(set(unsourced)),
        raw=raw,
    )