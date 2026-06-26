from __future__ import annotations
from .canonical import CanonicalState

def _dcf(inp: dict[str, float]) -> float:
    f1, f2 = inp["fcf_year1"], inp["fcf_year2"]
    r, g = inp["discount_rate"], inp["terminal_growth"]
    pv1 = f1 / (1 + r)
    pv2 = f2 / ((1 + r) ** 2)
    terminal = f2 * (1 + g) / (r - g) if r > g else 0.0
    pv_term = terminal / ((1 + r) ** 2)
    return round(pv1 + pv2 + pv_term, 6)

def score_world(state: CanonicalState, facts) -> dict:
    if "ALL_SOURCED" not in facts:
        return {"valuation": None, "input_count": len(state.inputs)}
    vals = {i.name: i.value for i in state.inputs}
    return {"valuation": _dcf(vals), "input_count": len(state.inputs)}
