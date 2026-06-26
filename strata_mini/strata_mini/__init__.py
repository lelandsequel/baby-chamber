"""STRATA-mini — a deterministic semantic decision layer (pattern extraction).

Not production STRATA. No LLMs at runtime. Pure stdlib core.
"""
from .bot import choose_action
from .canonical import CanonicalState, Entity, canonicalize
from .facts import CONFIG, derive_facts
from .gate import FinalDecision, REFUSED, RELEASED, gate
from .policy import ActionDecision, select_action
from .receipts import make_receipt
from .scoring import DIRECTIONS, score_world

__all__ = [
    "choose_action",
    "canonicalize", "CanonicalState", "Entity",
    "derive_facts", "CONFIG",
    "score_world", "DIRECTIONS",
    "select_action", "ActionDecision",
    "gate", "FinalDecision", "RELEASED", "REFUSED",
    "make_receipt",
]
__version__ = "0.1.0"
