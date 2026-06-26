# KEYSTONE-mini

Pattern extraction of KEYSTONE load-bearing integrity — **not** production KEYSTONE.
Contains none of its internals.

Refuses to **CLOSE** unless every required upstream receipt is present and its
`deterministic_receipt_hash` is recomputable from core fields.

```
upstream receipts → verify hashes → policy → gate → receipt
```

- **No LLMs at runtime.** Pure deterministic Python (stdlib only in core).
- **Same input + same config ⇒ same outcome, same receipt hash.**
- Synthetic fixtures only.

## Run tests

```bash
cd keystone_mini
PYTHONPATH=. python3 tests/test_bot_basic.py
```

## Output

`close(raw)` returns the gated close outcome and prints a deterministic receipt.

— KEYSTONE-mini · deterministic, receipted, refusal-first.
