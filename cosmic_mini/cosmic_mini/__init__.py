"""COSMIC-mini — trust-shell spine integration demo."""
from .bot import run, _pipeline_receipt
from .canonical import CanonicalState, Check, ValueField, canonicalize, synthetic_produce
from .facts import CONFIG, derive_facts
from .gate import REFUSED, RELEASED, FinalDecision, gate
from .policy import SpineDecision, select_action
from .receipts import make_receipt
from .scoring import score_world

__all__ = [
    "run", "_pipeline_receipt",
    "canonicalize", "CanonicalState", "ValueField", "Check", "synthetic_produce",
    "derive_facts", "CONFIG", "score_world", "select_action", "SpineDecision",
    "gate", "FinalDecision", "RELEASED", "REFUSED", "make_receipt",
]
__version__ = "0.1.0"
