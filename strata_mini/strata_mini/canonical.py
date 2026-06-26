"""Canonical state model + defensive parsing — STRATA-mini.

Turns a raw game tick / action-request (whatever shape it arrives in) into a
stable CanonicalState. No LLMs. No external calls. Pure stdlib. Never crashes on
missing optional fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Any, Optional


def _first(d: Any, keys: tuple[str, ...], default=None):
    """First present, non-None value among alternative key names."""
    if isinstance(d, dict):
        for k in keys:
            if k in d and d[k] is not None:
                return d[k]
    return default


def _num(d: Any, keys: tuple[str, ...], default: float = 0.0) -> float:
    v = _first(d, keys, default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _pos(value: Any) -> tuple[float, float]:
    """Parse a position from {x,y}, [x,y], (x,y) or 'x,y'. Defaults to (0,0)."""
    if isinstance(value, dict):
        return (_num(value, ("x", "X", "col", "c")), _num(value, ("y", "Y", "row", "r")))
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            return (float(value[0]), float(value[1]))
        except (TypeError, ValueError):
            return (0.0, 0.0)
    if isinstance(value, str) and "," in value:
        try:
            x, y = value.split(",")[:2]
            return (float(x), float(y))
        except ValueError:
            return (0.0, 0.0)
    return (0.0, 0.0)


@dataclass
class Entity:
    id: str
    type: str
    position: tuple[float, float]
    distance: float
    nutrinium: float = 0.0
    density: float = 1.0
    team: Optional[str] = None
    raw: dict = field(default_factory=dict)


@dataclass
class CanonicalState:
    tick: int
    ship_id: str
    position: tuple[float, float]
    energy: float
    max_energy: float
    cargo_nutrinium: float
    cargo_capacity: float
    destroyed: bool
    recharging: bool
    health: Optional[float]
    visible_asteroids: list[Entity]
    visible_trading_posts: list[Entity]
    visible_ships: list[Entity]
    visible_wreckage: list[Entity]
    raw: dict


def _entity(raw: dict, etype: str, ship_pos: tuple[float, float]) -> Entity:
    pos = _pos(_first(raw, ("position", "pos", "location", "coords"), {}))
    dist = _first(raw, ("distance", "dist", "range"), None)
    if dist is None:
        dist = hypot(pos[0] - ship_pos[0], pos[1] - ship_pos[1])
    return Entity(
        id=str(_first(raw, ("id", "uuid", "name"), "")),
        type=etype,
        position=pos,
        distance=float(dist),
        nutrinium=_num(raw, ("nutrinium", "ore", "value", "amount")),
        density=_num(raw, ("density", "richness"), 1.0),
        team=_first(raw, ("team", "owner", "faction")),
        raw=raw if isinstance(raw, dict) else {},
    )


def _entities(container: Any, etype: str, ship_pos) -> list[Entity]:
    if not isinstance(container, list):
        return []
    out = [_entity(e, etype, ship_pos) for e in container if isinstance(e, dict)]
    out.sort(key=lambda e: (e.distance, e.id))  # stable: nearest first, id tie-break
    return out


def canonicalize(raw_request: dict) -> CanonicalState:
    raw = raw_request if isinstance(raw_request, dict) else {}
    ship = _first(raw, ("ship", "self", "me", "player"), {})
    ship = ship if isinstance(ship, dict) else {}
    ship_src = {**raw, **ship}  # tolerate ship fields living at the top level

    position = _pos(_first(ship_src, ("position", "pos", "location", "coords"), {}))
    cargo = _first(ship_src, ("cargo", "hold", "inventory"), {})
    cargo = cargo if isinstance(cargo, dict) else {}
    cargo_view = {**ship_src, **cargo}  # cargo wins for nutrinium/capacity

    visible = _first(raw, ("visible", "sensors", "scan", "world"), raw)
    visible = visible if isinstance(visible, dict) else {}

    return CanonicalState(
        tick=int(_num(raw, ("tick", "turn", "frame", "step"), 0)),
        ship_id=str(_first(ship_src, ("id", "ship_id", "uuid"), "ship")),
        position=position,
        energy=_num(ship_src, ("energy", "power", "fuel"), 0.0),
        max_energy=_num(ship_src, ("max_energy", "energy_max", "max_power"), 100.0),
        cargo_nutrinium=_num(cargo_view, ("nutrinium", "cargo_nutrinium", "ore"), 0.0),
        cargo_capacity=_num(cargo_view, ("capacity", "cargo_capacity", "max_cargo"), 100.0),
        destroyed=bool(_first(ship_src, ("destroyed", "dead", "is_destroyed"), False)),
        recharging=bool(_first(ship_src, ("recharging", "is_recharging", "charging"), False)),
        health=_first(ship_src, ("health", "hp", "hull"), None),
        visible_asteroids=_entities(
            _first(visible, ("asteroids", "visible_asteroids"), []), "asteroid", position),
        visible_trading_posts=_entities(
            _first(visible, ("trading_posts", "tradingposts", "visible_trading_posts", "ports"), []),
            "trading_post", position),
        visible_ships=_entities(
            _first(visible, ("ships", "visible_ships", "other_ships"), []), "ship", position),
        visible_wreckage=_entities(
            _first(visible, ("wreckage", "visible_wreckage", "debris"), []), "wreckage", position),
        raw=raw,
    )
