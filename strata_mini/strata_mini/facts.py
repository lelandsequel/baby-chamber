"""Deterministic semantic fact derivation — STRATA-mini.

Same state + same CONFIG -> same facts, every time. Facts are plain strings so
the layer above can reason about meaning, not raw numbers.
"""
from __future__ import annotations

from .canonical import CanonicalState

# Tunable thresholds. "Same input + same config => same output" — change these
# and behaviour changes deterministically.
CONFIG = {
    "energy_critical_pct": 0.15,
    "energy_low_pct": 0.35,
    "recharge_target_pct": 0.90,
    "cargo_near_full_pct": 0.80,
    "cargo_meaningful": 1.0,          # min nutrinium worth a sell run
    "rich_asteroid_nutrinium": 50.0,
    "at_distance": 1.0,              # distance <= this counts as "at" an entity
    "hostile_distance": 20.0,
    "sell_pressure_high_pct": 0.50,
}


def _nearest(entities):
    return entities[0] if entities else None  # entities arrive sorted by distance, id


def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
    f: set[str] = set()
    max_e = state.max_energy or 1.0
    cap = state.cargo_capacity or 1.0

    if state.destroyed:
        f.add("SHIP_DESTROYED")
    if state.recharging:
        f.add("RECHARGING")

    e_ratio = state.energy / max_e
    if e_ratio <= config["energy_critical_pct"]:
        f.add("ENERGY_CRITICAL")
    elif e_ratio <= config["energy_low_pct"]:
        f.add("ENERGY_LOW")
    else:
        f.add("ENERGY_OK")

    cargo = state.cargo_nutrinium
    if cargo < config["cargo_meaningful"]:
        f.add("CARGO_EMPTY")
    else:
        f.add("CARGO_HAS_VALUE")
    if cargo >= cap * config["cargo_near_full_pct"]:
        f.add("CARGO_NEAR_FULL")

    asteroids = [a for a in state.visible_asteroids if a.nutrinium > 0]
    posts = state.visible_trading_posts

    near_ast = _nearest(asteroids)
    if near_ast is not None and near_ast.distance <= config["at_distance"]:
        f.add("AT_ASTEROID")
    near_post = _nearest(posts)
    if near_post is not None and near_post.distance <= config["at_distance"]:
        f.add("AT_TRADING_POST")

    if asteroids:
        f.add("ASTEROID_VISIBLE")
    if any(a.nutrinium >= config["rich_asteroid_nutrinium"] for a in asteroids):
        f.add("RICH_ASTEROID_VISIBLE")
    if posts:
        f.add("TRADING_POST_VISIBLE")
    if state.visible_wreckage:
        f.add("WRECKAGE_VISIBLE")

    # Placeholder until real team/friend-foe semantics arrive: any ship in range
    # is treated conservatively as a reason not to sit still and mine.
    if any(s.distance <= config["hostile_distance"] for s in state.visible_ships):
        f.add("HOSTILE_NEARBY")

    if "AT_ASTEROID" in f and "CARGO_NEAR_FULL" not in f and "HOSTILE_NEARBY" not in f:
        f.add("SAFE_TO_MINE")

    if "CARGO_HAS_VALUE" in f:
        if "CARGO_NEAR_FULL" in f or cargo >= cap * config["sell_pressure_high_pct"]:
            f.add("SELL_PRESSURE_HIGH")
        else:
            f.add("SELL_PRESSURE_LOW")

    return frozenset(f)
