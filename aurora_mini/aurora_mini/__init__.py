"""AURORA-mini — verdict gate pattern extraction."""
from .bot import verdict
from .canonical import CanonicalState, Check, canonicalize
from .facts import CONFIG, derive_facts
from .gate import REFUSED, RELEASED, FinalDecision, gate
from .policy import VerdictDecision, select_action
from .receipts import make_receipt
from .scoring import score_world

__all__ = [
    "verdict", "canonicalize", "CanonicalState", "Check",
    "derive_facts", "CONFIG", "score_world", "select_action", "VerdictDecision",
    "gate", "FinalDecision", "RELEASED", "REFUSED", "make_receipt",
]
__version__ = "0.1.0"
