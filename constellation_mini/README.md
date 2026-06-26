# CONSTELLATION-mini

Pattern extraction of CONSTELLATION drift measurement — **not** production CONSTELLATION.
Contains none of its internals.

Given a **signed bedrock baseline** and a **current sample**, computes deterministic
drift distance and refuses when past threshold. **Re-anchor to signed bedrock is never
permitted.**

```
baseline + sample → canonicalize → distance → policy → gate → receipt
```

- **No LLMs at runtime.** Pure deterministic Python (stdlib only in core).
- **Same input + same config ⇒ same distance, same outcome, same receipt hash.**
- Synthetic fixtures only.

## Run tests

```bash
cd constellation_mini
PYTHONPATH=. python3 tests/test_bot_basic.py
```

## Output

`measure(raw)` returns the gated drift outcome and prints a deterministic receipt.

— CONSTELLATION-mini · deterministic, receipted, refusal-first.
