# COSMIC-mini

Pattern extraction of COSMIC trust-shell integration — **not** production COSMIC.
Contains none of its internals.

Wires the spine end-to-end (standalone, inline — no sibling package imports):

```
produce → VELLUM envelope → AURORA gate → LUNA witness → receipt
```

- **No LLMs at runtime.** Pure deterministic Python (stdlib only in core).
- **Same input + same config ⇒ same facts, same outcome, same receipt hash.**
- Synthetic fixtures only. `generate: true` feeds the synthetic producer.

## Run tests

```bash
cd cosmic_mini
PYTHONPATH=. python3 tests/test_bot_basic.py
```

## Output

`run(raw)` returns the gated spine outcome and prints a deterministic receipt with
`deterministic_receipt_hash` (sha256, sorted keys, no timestamps).

— COSMIC-mini · deterministic, receipted, refusal-first.
