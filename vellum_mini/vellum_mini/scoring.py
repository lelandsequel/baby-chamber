"""Score envelope candidates — VELLUM-mini."""
from __future__ import annotations

from .canonical import CanonicalState


def score_world(state: CanonicalState, facts) -> dict:
    envelopes = [
        {"name": fld.name, "value": fld.value, "source": fld.source, "sha": fld.sha}
        for fld in state.fields
    ]
    return {
        "envelopes": envelopes,
        "envelope_count": len(envelopes),
        "refused_count": len(state.unsourced_fields),
        "unsourced_fields": list(state.unsourced_fields),
    }