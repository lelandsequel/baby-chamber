"""Mode + action selection — the priority ladder. STRATA-mini.

Pick a MODE first, then the action it implies. Pure function of (state, facts,
scores). No side effects.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .canonical import CanonicalState
from .facts import CONFIG
from .scoring import direction_to, explore_direction


@dataclass
class ActionDecision:
    action: str
    payload: dict = field(default_factory=dict)
    reason: str = ""
    mode: str = "EXPLORE"
    priority: int = 0


def _move_to(state, entity, mode, reason, priority) -> ActionDecision:
    if entity is None:
        return ActionDecision("MOVE", {"direction": explore_direction(state)}, reason, mode, priority)
    return ActionDecision(
        "MOVE",
        {"direction": direction_to(state.position, entity.position),
         "target_id": entity.id,
         "target": list(entity.position)},
        reason, mode, priority,
    )


def select_action(state: CanonicalState, facts, scores, config: dict = CONFIG) -> ActionDecision:
    F = facts

    # 1. destroyed -> respawn
    if "SHIP_DESTROYED" in F:
        return ActionDecision("RESPAWN", {}, "ship destroyed", "RESPAWN", 100)

    # 2 / 3. recharging
    if "RECHARGING" in F:
        target = state.max_energy * config["recharge_target_pct"]
        if state.energy < target:
            return ActionDecision("WAIT", {"reason": "charging"}, "recharging below target", "WAIT_SAFE", 95)
        return ActionDecision("RECHARGE_END", {}, "recharge target reached", "RECHARGE", 95)

    # 4. energy critical -> recharge
    if "ENERGY_CRITICAL" in F:
        return ActionDecision("RECHARGE", {}, "energy critical", "RECHARGE", 90)

    # 5. carrying value AND at a trading post -> sell
    if "CARGO_HAS_VALUE" in F and "AT_TRADING_POST" in F:
        post = scores.get("_best_post_entity")
        return ActionDecision("SELL", {"target_id": post.id if post else None},
                              "at trading post with cargo", "SELL_RUN", 80)

    # 6. carrying value AND a post is visible -> move to sell
    if "CARGO_HAS_VALUE" in F and "TRADING_POST_VISIBLE" in F:
        return _move_to(state, scores.get("_best_post_entity"), "SELL_RUN", "moving to sell cargo", 70)

    # 7. on a nutrinium asteroid, cargo not near full -> mine
    if "AT_ASTEROID" in F and "CARGO_NEAR_FULL" not in F:
        return ActionDecision("MINE", {}, "mining local asteroid", "MINE_LOCAL", 60)

    # 8. asteroid visible -> move toward best
    if "ASTEROID_VISIBLE" in F:
        return _move_to(state, scores.get("_best_asteroid_entity"), "SEEK_ASTEROID", "seeking asteroid", 50)

    # 9. nothing else -> deterministic exploration move
    return ActionDecision("MOVE", {"direction": explore_direction(state)}, "exploring", "EXPLORE", 10)
