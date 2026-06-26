"""Deterministic scoring + direction helpers — STRATA-mini.

No randomness anywhere. Exploration is derived from (tick + position hash) so the
same tick at the same place always yields the same move.
"""
from __future__ import annotations

import hashlib

from .canonical import CanonicalState, Entity

DIRECTIONS = ("NORTH", "EAST", "SOUTH", "WEST")  # stable ordering
# Coordinate convention: NORTH = +y, SOUTH = -y, EAST = +x, WEST = -x.


def _round(x: float) -> float:
    return round(float(x), 6)


def asteroid_score(a: Entity) -> float:
    """Value per unit distance, boosted by density when available."""
    base = a.nutrinium / max(a.distance, 1.0)
    density = a.density if a.density and a.density > 0 else 1.0
    return base * density


def pos_hash(position) -> int:
    key = f"{_round(position[0])},{_round(position[1])}"
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16)


def explore_direction(state: CanonicalState) -> str:
    idx = (int(state.tick) + pos_hash(state.position)) % len(DIRECTIONS)
    return DIRECTIONS[idx]


def direction_to(frm, to) -> str:
    dx = to[0] - frm[0]
    dy = to[1] - frm[1]
    if abs(dx) >= abs(dy):
        return "EAST" if dx >= 0 else "WEST"
    return "NORTH" if dy > 0 else "SOUTH"


def score_world(state: CanonicalState, facts) -> dict:
    asteroids = [a for a in state.visible_asteroids if a.nutrinium > 0]
    scored_ast = sorted(
        ((a, asteroid_score(a)) for a in asteroids),
        key=lambda t: (-t[1], t[0].id),  # best score, id tie-break
    )
    best_ast = scored_ast[0] if scored_ast else None

    posts = sorted(state.visible_trading_posts, key=lambda p: (p.distance, p.id))
    best_post = posts[0] if posts else None

    return {
        "asteroids": [(a.id, _round(s)) for a, s in scored_ast],
        "best_asteroid": [best_ast[0].id, _round(best_ast[1])] if best_ast else None,
        "trading_posts": [(p.id, _round(p.distance)) for p in posts],
        "best_trading_post": [best_post.id, _round(best_post.distance)] if best_post else None,
        "explore_direction": explore_direction(state),
        # private handles (not serialized into receipts)
        "_best_asteroid_entity": best_ast[0] if best_ast else None,
        "_best_post_entity": best_post if best_post else None,
    }
