#!/usr/bin/env python3
"""Scaffold all baby-chamber packages. Run once from baby-chamber root."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LICENSE = (ROOT / "LICENSE").read_text() if (ROOT / "LICENSE").exists() else """MIT License

Copyright (c) 2026 Leland Jourdan II / JourdanLabs

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

GITIGNORE = """__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/
.DS_Store
*.egg-info/
build/
dist/
"""


def w(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"))


def receipt_module() -> str:
    return '''
    """Deterministic receipts — sha256 over sorted keys, no timestamps."""
    from __future__ import annotations

    import hashlib
    import json


    def receipt_hash(core: dict) -> str:
        return hashlib.sha256(
            json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


    def finalize_core(core: dict) -> dict:
        digest = receipt_hash(core)
        return {**core, "deterministic_receipt_hash": digest}
    '''


def gate_boilerplate(verdict_released: str = "RELEASED", verdict_refused: str = "REFUSED_WITH_FALLBACK") -> str:
    return f'''
    """Validation gate + safe fallback."""
    from __future__ import annotations

    from dataclasses import dataclass

    RELEASED = "{verdict_released}"
    REFUSED = "{verdict_refused}"


    @dataclass
    class FinalDecision:
        outcome: str
        payload: dict
        reason: str
        verdict: str = RELEASED
        refusal_reason: str = ""
        candidate_outcome: str = ""

        def to_response(self) -> dict:
            return {{
                "outcome": self.outcome,
                "payload": self.payload,
                "reason": self.reason,
                "verdict": self.verdict,
            }}
    '''


def test_boilerplate(pkg: str, entry_fn: str, valid_fixture: str, refusal_test_body: str) -> str:
    return f'''
    """Acceptance tests for {pkg}. Plain assert — no pytest required."""
    import io
    import json
    import pathlib
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

    from {pkg}.bot import {entry_fn}
    from {pkg}.gate import REFUSED

    FIX = pathlib.Path(__file__).parent / "fixtures"


    def load(name):
        return json.loads((FIX / name).read_text())


    def run_all():
        for n in sorted(x for x in globals() if x.startswith("test_")):
            globals()[n]()
            print("PASS", n)


    def test_determinism_same_input_twice():
        raw = load("{valid_fixture}")
        assert {entry_fn}(raw) == {entry_fn}(raw)


    {refusal_test_body}


    def test_receipt_hash_stable():
        import contextlib
        from {pkg}.bot import _pipeline_receipt
        raw = load("{valid_fixture}")
        h1 = _pipeline_receipt(raw)["deterministic_receipt_hash"]
        h2 = _pipeline_receipt(raw)["deterministic_receipt_hash"]
        assert h1 == h2
        assert len(h1) == 64


    if __name__ == "__main__":
        run_all()
    '''


PACKAGES = {}  # filled below