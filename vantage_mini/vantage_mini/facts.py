from __future__ import annotations
from .canonical import CanonicalState

CONFIG = {}
PATTERNS = (
    ("BARE_EXCEPT", "except:"),
    ("EVAL_USAGE", "eval("),
    ("PRINT_DEBUG", "print("),
    ("HARDCODED_SECRET", "password ="),
)

def derive_facts(state: CanonicalState, config: dict = CONFIG) -> frozenset[str]:
    f: set[str] = set()
    src = state.source
    hits = []
    for name, needle in PATTERNS:
        if needle in src:
            hits.append(name)
            f.add(f"SMELL_{name}")
    if hits:
        f.add("HAS_FINDINGS")
    f.add("ALL_PATTERNS_CHECKED")
    f.add(f"PATTERN_COUNT_{len(PATTERNS)}")
    return frozenset(f)
